#
# Regular cron jobs for the fileaccessmonitor package
#
0 4	* * *	root	[ -x /usr/bin/fileaccessmonitor_maintenance ] && /usr/bin/fileaccessmonitor_maintenance
