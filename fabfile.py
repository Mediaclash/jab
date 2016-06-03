from fabric.api import cd, env, run, sudo, task, execute, settings, local
import fabric
from fabric.contrib.files import exists, append, comment, contains
from fabric.contrib.console import confirm
from fabric.colors import blue, cyan, green, red, blue, yellow
import os, json
from jira import JIRA
from datetime import datetime

jac = JIRA('https://mediaclash.atlassian.net')

def format_jira_time(timedelta):
    ts = timedelta.total_seconds()
    m, s = divmod(ts, 60)
    h, m = divmod(m, 60)
    if h:
        return '%(h)ih%(m)im' % locals()
    else:
        return '%(m)im' % locals()


def get_jirawork():
    if not os.path.isfile('.jirawork'):
        print red('No Worklog found, did you forget to fab start:<issue_number>?')
        exit()
    with open('.jirawork', 'r') as f:
        data = json.load(f)
    return data


def get_commit_log_from_work(comment):
    data = get_jirawork()
    start = datetime.strptime(data['start'], '%Y-%m-%d %H:%M:%S.%f')
    now = datetime.now()
    elapsed = now - start
    timestring = format_jira_time(elapsed)
    issue = data['issue']
    commit_log = '%(issue)s #comment %(comment)s #time %(timestring)s' % locals()
    return commit_log

def get_issue(issue_number):
	return jac.issue(issue_number)


def get_current_issue():
    data = get_jirawork()
    issue = jac.issue(data['issue'])
    return issue



def get_time_spent():
    data = get_jirawork()
    start = datetime.strptime(data['start'], '%Y-%m-%d %H:%M:%S.%f')
    now = datetime.now()
    elapsed = now - start
    timestring = format_jira_time(elapsed)
    return timestring


@task
def todo(limit=10):
	'''
	Get a list of issues assigned to me
	'''
	#jac = JIRA('https://mediaclash.atlassian.net')
	issues = jac.search_issues('assignee = currentUser() AND resolution = Unresolved AND NOT status = Backlog AND NOT status = Done order by priority, updated DESC', maxResults=limit)
	for issue in issues:
		print blue(issue.key), yellow(issue.fields.priority), green(issue.fields.summary)

@task
def info(issue_number):
	'''
	Get info about a ticket
	'''

@task
def start(issue_number):
	'''
	Start work on an issue
	'''
	if os.path.isfile('.jirawork'):
	    with open('.jirawork', 'r') as f:
	        data = json.load(f)
	        print red('Already working on %(issue)s, please fab done first or delete .jirawork' % data)
	    return


	#jac = JIRA('https://mediaclash.atlassian.net')
	issue = jac.issue(issue_number)
	print 'Working on - ' + green(issue.key) + ' : ' + blue(issue.fields.summary)
	timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
	data = {'issue':issue_number, 'start':timestamp}
	with open('.jirawork', 'w') as f:
		f.write(json.dumps(data))



@task
def doing():
    '''
    Show current issue being in progress
    '''
    issue = get_current_issue()
    time = get_time_spent()
    key = issue.key

    print 'Working on - ' + green(issue.key) + ' : ' + blue(issue.fields.summary) + ' for ' + time


@task
def cancel():
	'''
	Stop tracking without logging work
	'''
	data = get_jirawork()
	time = get_time_spent()
	issue = data['issue']

	print blue('Logged %(time)s on %(issue)s' % locals())
	if confirm('Disgard this work?'):
		os.remove('.jirawork')




@task
def qa(comment, issue=None):
    '''
    Assign the current issue to it's reporter with a comment and log any work
    '''
    if not issue:
    	data = get_jirawork()
    	issue = data['issue']
    #jac = JIRA('https://mediaclash.atlassian.net')
    jira_issue = jac.issue(issue)
    jac.add_comment(jira_issue, '%(comment)s\n\nPlease Test.' % locals())
    jac.assign_issue(jira_issue, jira_issue.fields.reporter.key)
    try:
    	os.remove('.jirawork')
    except:
    	pass
    print 'Assigned ' + red(issue.key) + ' to ' + green(str(jira_issue.fields.reporter)) + ' for QA'


@task
def commit(comment):
    '''
    Generate a commit message using the work log

    '''
    if not os.path.isfile('.jirawork'):
        print red('No Worklog found, did you forget to fab start:<issue_number>?')
        return
    commit_log = get_commit_log_from_work(comment)
    print "Will Commit: " + blue(commit_log)
    if confirm('Ok?'):
    	local('git commit -m "%(commit_log)s"' % locals())
    	os.remove('.jirawork')

@task
def work(comment='worked'):
	'''
	Log time and stop work
	'''
	data = get_jirawork()
	#jac = JIRA('https://mediaclash.atlassian.net')
	start = datetime.strptime(data['start'], '%Y-%m-%d %H:%M:%S.%f')
	now = datetime.now()
	elapsed = now - start
	timestring = format_jira_time(elapsed)
	issue = data['issue']
	commit_log = '%(issue)s #comment %(comment)s #time %(timestring)s' % locals()
	print blue(commit_log)
	jac.add_worklog(issue, timeSpent=timestring, comment=comment)
	os.remove('.jirawork')
	print green('Done')

        




