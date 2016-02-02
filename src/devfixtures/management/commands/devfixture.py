import subprocess
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from os.path import join, realpath, relpath, split
import getpass
import re
from datetime import datetime
import shutil
import tempfile
from os import listdir
from os.path import isfile, join, basename


class Command(BaseCommand):

    help = 'Development fixture manager'

    def add_arguments(self, parser):
        default_fixtures_dir = relpath(getattr(
            settings, 'DKISS_EXT_DEVFIXTURE_DIR',
            join(settings.BASE_DIR, '..', 'dev_fixtures')
        ))
        default_backup_dir = relpath(getattr(
            settings, 'DKISS_EXT_DEVFIXTURE_BACKUP_DIR',
            join(settings.BASE_DIR, '..', '.dev_fixtues_backup')
        ))

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
        # TODO: check that we have MEDIA_ROOT defined
        self._fixture_dir = realpath(options['fixtures_dir'])
        self._backup_dir = realpath(options['backup_dir'])
        self._database_name = settings.DATABASES['default']['NAME']
        self._media_root = settings.MEDIA_ROOT
        self._media_file_basename = basename(self._media_root)

        if options['action'] == 'create':
            fixture_file = options['fixture_file'] or join(self._fixture_dir, self._build_fixture_file_name())
            self._create_fixture(fixture_file)
        elif options['action'] == 'restore':
            backup_fixture_file = join(self._backup_dir, self._build_fixture_file_name())
            self.write_info('Backing up to %s' % backup_fixture_file)
            self._create_fixture(backup_fixture_file)
            self.write_info('... backup complete')
            fixture_file = options['fixture_file'] or self._find_best_match()
            self._restore_fixture(fixture_file)
        else:
            raise CommandError('action can only be create or restore')

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
        commit_list = subprocess.check_output(['git', 'log', '--pretty=format:%h']).splitlines(False)
        fixture_files_per_commit = self._fixture_files_per_commit()
        for commit in commit_list:
            if commit in fixture_files_per_commit:
                # returing the latests file
                return sorted([realpath(f) for f in fixture_files_per_commit[commit]], reverse=True)[0]
        raise CommandError('Could not find a best match fixture')

    def _restore_fixture(self, fixture_file):
        try:
            tmp_dir = tempfile.mkdtemp()
            self.write_debug('Restore tmp dir %s' % tmp_dir)
            self.write_debug(subprocess.check_output(['unzip', fixture_file, '-d', tmp_dir]))
            self.write_info('Restoring fixture %s' % fixture_file)
            self.write_debug('Deleting %s' % self._media_root)
            shutil.rmtree(self._media_root)
            self.write_debug('... done deleting')
            self.write_debug('Create new media root')
            shutil.copytree(join(tmp_dir, self._media_file_basename), self._media_root)
            self.write_debug('... done creating new media root')
            self.write_debug('Restoring database')
            subprocess.check_output(['dropdb', self._database_name])
            subprocess.check_output(['createdb', self._database_name])
            with open(join(tmp_dir, 'db.sql')) as fp:
                subprocess.check_output(['psql', self._database_name], stdin=fp)
            self.write_debug('... database restored')
        except:
            raise
        else:
            self.write_info('... fixture restored')
        finally:
            pass

    def _create_fixture(self, fixture_file_path):
        try:
            self.write_info('Creating fixture %s' % fixture_file_path)
            fixture_file_path = re.sub(r'\.zip$', '', fixture_file_path)  # we strip away .zip if given
            tmp_dir = tempfile.mkdtemp()
            # copy media root
            shutil.copytree(self._media_root, join(tmp_dir, split(self._media_root)[1]))
            # database dump
            with open(join(tmp_dir, 'db.sql'), 'w') as fp:
                subprocess.call(['pg_dump', '--clean', '--no-owner', self._database_name], stdout=fp)
            # creating the fixture archive
            archive_name = shutil.make_archive(fixture_file_path, 'zip', root_dir=tmp_dir)
            self.write_debug(subprocess.check_output(['unzip', '-l', archive_name]))
        except:
            # shutil.rmtree(tmp_dir)
            raise
        else:
            self.write_info('... fixture created')
        finally:
            pass
            # shutil.rmtree(tmp_dir)

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

    def write_info(self, msg):
        self.stdout.write(msg)

    def write_debug(self, msg):
        self.stderr.write(msg)
