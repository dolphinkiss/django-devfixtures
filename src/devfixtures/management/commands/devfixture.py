import getpass
import re
import shutil
import subprocess
import tempfile
import traceback
from datetime import datetime
from distutils.spawn import find_executable
from os import listdir
from os.path import isfile, join, basename, realpath, relpath, isdir

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

REQUIRED_EXEC = ['psql', 'dropdb', 'createdb', 'unzip', 'pg_dump', 'git']


class Command(BaseCommand):

    help = 'Development fixture manager'

    def add_arguments(self, parser):
        default_fixtures_dir = relpath(settings.DEVFIXTURE_DIR)
        default_backup_dir = relpath(settings.DEVFIXTURE_BACKUP_DIR)

        parser.add_argument('action', choices=['create', 'restore'])
        parser.add_argument(
            '-d', '--fixtures-dir',
            default=default_fixtures_dir,
            help='Fixtures directory. [default: %(default)s]'
        )
        parser.add_argument(
            '-b', '--backup-dir',
            default=default_backup_dir,
            help='Backup directory. [default: %(default)s]'
        )
        parser.add_argument(
            '-f', '--fixture-file',
            required=False,
            help='File to use to create/restore from. Note that if you use this, some of the auto detection'
                 'features will not function properly'
        )

    def handle(self, *args, **options):

        self._check_dependencies()

        # TODO: if MEDIA_ROOT is not set, maybe we should allow it anyways, and just do the db dump
        if not hasattr(settings, 'MEDIA_ROOT'):
            raise CommandError('MEDIA_ROOT needs to be set to use devfixtures')

        self._media_root = realpath(settings.MEDIA_ROOT)
        self._media_root_basename = basename(self._media_root)
        self._fixture_dir = realpath(options['fixtures_dir'])
        self._backup_dir = realpath(options['backup_dir'])
        self._database_name = settings.DATABASES['default']['NAME']
        self._verbosity = options['verbosity']

        if not isdir(self._media_root):
            raise CommandError('MEDIA_ROOT %s does not exist' % self._media_root)

        if options['action'] == 'create':
            self._create(options['fixture_file'] or join(self._fixture_dir, self._build_fixture_file_name()))
        elif options['action'] == 'restore':
            if not options['fixture_file'] and not isdir(self._fixture_dir):
                raise CommandError('Fixture dir %s does not exist, did you generate any fixtures before?')
            fixture_file = options['fixture_file'] or self._find_best_match()
            backup_fixture_file = self._backup()
            try:
                self._restore(fixture_file)
            except Exception:
                self.write_info('Restore failed, trying to restore backup.', 0)
                self.stderr.write('----- EXCEPTION -----')
                self.stderr.write(traceback.format_exc())
                self.stderr.write('----- EXCEPTION END -----')
                try:
                    self._restore(backup_fixture_file)
                except Exception:
                    self.stderr.write('----- EXCEPTION -----')
                    self.stderr.write(traceback.format_exc())
                    self.stderr.write('----- EXCEPTION END -----')
                    raise CommandError('Failed to restore backup fixture %s' % backup_fixture_file)
                else:
                    self.write_info('... restore completed', 0)
        else:
            raise CommandError('action can only be create or restore')

    def _create(self, fixture_file_path, less_verbose=0):
        try:
            self.write_info('Creating fixture %s' % fixture_file_path, 1+less_verbose)
            fixture_file_path = re.sub(r'\.zip$', '', fixture_file_path)  # we strip away .zip if given
            tmp_dir = tempfile.mkdtemp()
            # copy media root
            shutil.copytree(self._media_root, join(tmp_dir, 'MEDIA_ROOT'))
            # database dump
            with open(join(tmp_dir, 'db.sql'), 'w') as fp:
                subprocess.call(['pg_dump', '--clean', '--no-owner', self._database_name], stdout=fp)
            # creating the fixture archive
            archive_name = shutil.make_archive(fixture_file_path, 'zip', root_dir=tmp_dir)
            self.write_debug(subprocess.check_output(['unzip', '-l', archive_name]))
        except:
            self.write_debug('Temporary directory %s kept due to exception.' % tmp_dir)
            raise
        else:
            self.write_info('... fixture created', 1+less_verbose)
            shutil.rmtree(tmp_dir)

    def _restore(self, fixture_file):
        try:
            tmp_dir = tempfile.mkdtemp()
            self.write_debug('Restore tmp dir: %s' % tmp_dir)
            self.write_debug(subprocess.check_output(['unzip', fixture_file, '-d', tmp_dir]))
            self.write_info('Restoring fixture %s' % fixture_file, 1)
            self.write_debug('Deleting %s' % self._media_root)
            shutil.rmtree(self._media_root)
            self.write_debug('... done deleting')
            self.write_debug('Create new media root')
            shutil.copytree(join(tmp_dir, 'MEDIA_ROOT'), self._media_root)
            self.write_debug('... done creating new media root')
            self.write_debug('Drop and create database')
            subprocess.check_output(['dropdb', self._database_name])
            subprocess.check_output(['createdb', self._database_name])
            self.write_debug('... drop/create done')
            self.write_debug('Restoring database')
            with open(join(tmp_dir, 'db.sql')) as fp:
                subprocess.check_output(['psql', self._database_name], stdin=fp)
            self.write_debug('... database restored')
        except:
            self.write_debug('Temporary directory %s kept due to exception.' % tmp_dir)
            raise
        else:
            self.write_info('... fixture restored', 1)
            shutil.rmtree(tmp_dir)

    def _backup(self):
        backup_fixture_file = join(self._backup_dir, self._build_fixture_file_name())
        self.write_info('Backing up to %s' % backup_fixture_file, 1)
        self._create(backup_fixture_file, less_verbose=1)
        self.write_info('... backup complete', 1)
        return backup_fixture_file

    def _check_dependencies(self):
        not_found = []
        for executable in REQUIRED_EXEC:
            if not find_executable(executable):
                not_found.append(executable)
        if not_found:
            raise CommandError('The following executables are required: %s, missing: %s' % (REQUIRED_EXEC, not_found))

    def _fixture_files_per_commit(self):
        files_per_commit = {}
        for file_name in listdir(self._fixture_dir):
            path = join(self._fixture_dir, file_name)
            if not isfile(path):
                continue
            commit = file_name.split('+')[1]
            files_per_commit.setdefault(commit, []).append(realpath(path))
        return files_per_commit

    def _find_best_match(self):
        """
        This function checks the fixture_dir for the latest fixture using commits backwards starting from
        HEAD and back.
        """
        fixture_files_per_commit = self._fixture_files_per_commit()
        if not fixture_files_per_commit:
            raise CommandError('There are no autogenerated fixtures in %s' % self._fixture_dir)
        commit_list = subprocess.check_output(['git', 'log', '--pretty=format:%h']).splitlines(False)
        for commit in commit_list:
            if commit in fixture_files_per_commit:
                # returing the latests file
                return sorted([realpath(f) for f in fixture_files_per_commit[commit]], reverse=True)[0]
        raise CommandError('Could not find a best match fixture')

    def _build_fixture_file_name(self):

        def commit_author_date(commit):
            cmd_output = subprocess.check_output(['git', 'show', '-s', '--format=%ai', head_commit]).strip()
            cmd_output = re.sub(r'\s*\+.*', '', cmd_output)
            cmd_output = re.sub(r'\s+', 'T', cmd_output)
            return cmd_output

        head_commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip()
        format_args = {
            'commit_date': commit_author_date(head_commit),
            'commit': head_commit,
            'run_date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
            'user': getpass.getuser(),
        }
        return '%(commit_date)s+%(commit)s+%(run_date)s+%(user)s.zip' % format_args

    def write_info(self, msg, verbose_level):
        if self._verbosity >= verbose_level:
            self.stdout.write(msg)

    def write_debug(self, msg):
        if self._verbosity == 3:
            self.stderr.write(msg)
