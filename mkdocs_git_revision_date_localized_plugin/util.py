import os
import logging
from git import Git
from datetime import datetime
from babel.dates import format_date


class Util:

    def __init__(self, path = "."):
        self.repo = Git(path)
        
        # Checks when running builds on CI
        # See https://github.com/timvink/mkdocs-git-revision-date-localized-plugin/issues/10
        if is_shallow_clone(self.repo):
            n_commits = commit_count(self.repo)

            if os.environ.get('GITLAB_CI') and n_commits < 50:
                logging.warning("""
                       Running on a gitlab runner might lead to wrong git revision dates
                       due to a shallow git fetch depth.  
                       Make sure to set GIT_DEPTH to 1000 in your .gitlab-ci.yml file.
                       (see https://docs.gitlab.com/ee/user/project/pipelines/settings.html#git-shallow-clone).
                       """)
            if os.environ.get('GITHUB_ACTIONS') and n_commits == 1:
                logging.warning("""
                       Running on github actions might lead to wrong git revision dates
                       due to a shallow git fetch depth. 
                       Try setting fetch-depth to 0 in your github action
                       (see https://github.com/actions/checkout).
                       """)

    @staticmethod
    def _date_formats(unix_timestamp, locale = 'en'):
        """
        Returns different date formats / types.
        
        Args:
            unix_timestamp (datetiment): a timestamp in seconds since 1970
            locale (str): Locale code of language to use. Defaults to 'en'.
            
        Returns:
            dict: different date formats
        """
        
        # Convert to millisecond timestamp
        unix_timestamp = int(unix_timestamp)
        timestamp_in_ms = unix_timestamp * 1000
        
        revision_date = datetime.utcfromtimestamp(unix_timestamp)
        
        return {
            'date' : format_date(revision_date, format="long", locale=locale), 
            'datetime' : format_date(revision_date, format="long", locale=locale) + ' ' +revision_date.strftime("%H:%M:%S"),
            'iso_date' : revision_date.strftime("%Y-%m-%d"), 
            'iso_datetime' : revision_date.strftime("%Y-%m-%d %H:%M:%S"), 
            'timeago' : "<span class='timeago' datetime='%s' locale='%s'></span>" % (timestamp_in_ms, locale)
        }
        

    def get_revision_date_for_file(self, path, locale = 'en'):
        """
        Determine localized date variants for a given file
        
        Args:
            path (str): Location of a markdownfile that is part of a GIT repository
            locale (str, optional): Locale code of language to use. Defaults to 'en'.
        
        Returns:
            dict: localized date variants 
        """
        
        unix_timestamp = self.repo.log(path, n=1, date='short', format='%at')
                    
        if not unix_timestamp:
            unix_timestamp = datetime.utcnow().timestamp()
            logging.warning('%s has no git logs, using current timestamp' % path)
        
        return self._date_formats(unix_timestamp)

def is_shallow_clone(repo):
    """
    Helper function to determine if repository 
    is a shallow clone.
    
    References:
    https://github.com/timvink/mkdocs-git-revision-date-localized-plugin/issues/10
    https://stackoverflow.com/a/37203240/5525118
    
    Args:
        repo (git.Repo): Repository
        
    Returns:
        bool: If a repo is shallow clone
    """
    return os.path.exists(".git/shallow")


def commit_count(repo):
    """
    Helper function to determine the number of commits in a repository
    
    Args:
        repo (git.Repo): Repository
        
    Returns:
        count (int): Number of commits
    """
    refs = repo.for_each_ref().split('\n')
    refs = [x.split()[0] for x in refs]

    counts = [int(repo.rev_list(x, count=True, first_parent=True)) for x in refs]
    return max(counts)