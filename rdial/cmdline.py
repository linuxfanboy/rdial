#
#
"""cmdline - Command line functionality for rdial"""
# Copyright (C) 2011-2012  James Rowe <jnrowe@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

# pylint: disable-msg=C0121

import argparse
import datetime
import os

import aaargh
import isodate
import prettytable

from .events import Events
from .i18n import (_, N_)
from . import _version
from . import utils

APP = aaargh.App(description=__doc__.splitlines()[0].split("-", 1)[1],
                 epilog=_("Please report bugs to jnrowe@gmail.com"))


class TaskAction(argparse.Action):

    """Define task name, handling --from-dir option."""

    def __call__(self, parser, namespace, values, option_string=None):
        if namespace.from_dir:
            namespace.task = os.path.basename(os.path.abspath(os.curdir))
        else:
            namespace.task = values


def task_name_typecheck(string):
    """Check given task name is valid.

    :param str string: Task name to check
    :rtype: str
    :returns: Task name, if valid
    :raises argparse.ArgparseTypeError: If task name is invalid

    """
    if '/' in string or '\000' in string:
        raise argparse.ArgumentTypeError(_('%r is not a valid task name')
                                         % string)
    return string


# pylint: disable-msg=C0103
task_parser = argparse.ArgumentParser(add_help=False)
names_group = task_parser.add_mutually_exclusive_group()
names_group.add_argument('-x', '--from-dir', action='store_true',
                         help=_('use directory name as task'))
names_group.add_argument('task', default='default', nargs='?',
                         action=TaskAction, help=_('task name'),
                         type=task_name_typecheck)

duration_parser = argparse.ArgumentParser(add_help=False)
duration_parser.add_argument('-d', '--duration', default='all',
                             choices=['day', 'week', 'month', 'year', 'all'],
                             help=_("filter events for specified time period"))
# pylint: enable-msg=C0103


def filter_events(directory, task=None, duration=None):
    """Filter events for report processing.

    :param argparse.Namespace args: Command line arguments
    :rtype: `Events`
    :return: Events matching criteria specified in ``args``

    """
    events = Events.read(directory)
    if task:
        events = events.for_task(task)
    if not duration == "all":
        if duration == "week":
            today = datetime.date.today()
            events = events.for_week(*today.isocalendar()[:2])
        else:
            year, month, day = datetime.date.today().timetuple()[:3]
            if duration == "month":
                day = None
            elif duration == "year":
                month = None
                day = None
            events = events.for_date(year, month, day)
    return events


def start_time_typecheck(string):
    """Check given start time is valid.

    :param str string: Timestamps to check
    :rtype: str
    :returns: Timestamp, if valid
    :raises argparse.ArgparseTypeError: If timestamp is invalid

    """
    try:
        utils.parse_datetime(string)
    except ValueError:
        raise argparse.ArgumentTypeError(_('%r is not a valid ISO-8601 time '
                                           'string') % string)
    return string


@APP.cmd(help=_("start task"), parents=[task_parser])
@APP.cmd_arg('-n', '--new', action='store_true', help=_('start a new task'))
@APP.cmd_arg('-t', '--time', metavar='time', default='',
             help=_('set start time'), type=start_time_typecheck)
def start(directory, task, new, time, from_dir):
    """Start task."""
    with Events.context(directory) as events:
        events.start(task, new, time)


@APP.cmd(help=_("stop task"))
@APP.cmd_arg('-m', '--message', metavar='message', help=_('closing message'))
@APP.cmd_arg('--amend', action='store_true',
             help=_('amend previous stop entry'))
def stop(directory, message, amend):
    """Stop task."""
    with Events.context(directory) as events:
        if amend and not message:
            event = events.last()
            message = event.message
        events.stop(message, force=amend)
    event = events.last()
    print(_('Task %s running for %s') % (event.task,
                                         str(event.delta).split('.')[0]))


# pylint: disable-msg=C0103
output_parser = argparse.ArgumentParser(add_help=False)
output_group = output_parser.add_mutually_exclusive_group()
output_group.add_argument('--html', action='store_true',
                          help=_('produce HTML output'))
output_group.add_argument('--human', action='store_true',
                          help=_('produce human-readable output'))
# pylint: ensable-msg=C0103


@APP.cmd(help=_("report time tracking data"),
         parents=[duration_parser, task_parser, output_parser])
@APP.cmd_arg('-s', '--sort', default='task', choices=['task', 'time'],
             help=_('field to sort by'))
@APP.cmd_arg('-r', '--reverse', action='store_true',
             help=_('reverse sort order'))
def report(directory, task, duration, sort, reverse, html, human, from_dir):
    """Report time tracking data."""
    if task == 'default':
        # Lazy way to remove duplicate argument definitions
        task = None
    events = filter_events(directory, task, duration)
    if human:
        print(N_('%d event in query', '%d events in query', len(events))
                 % len(events))
        print(_('Duration of events %s') % events.sum())
        print(_('First entry started at %s') % events[0].start)
        print(_('Last entry started at %s') % events[-1].start)
        dates = set(e.start.date() for e in events)
        print(_('Events exist on %d dates') % len(dates))
    else:
        table = prettytable.PrettyTable(['task', 'time'])
        formatter = table.get_html_string if html else table.get_string
        try:
            table.align['task'] = 'l'
        except AttributeError:  # prettytable 0.5 compatibility
            table.set_field_align('task', 'l')
        for task in events.tasks():
            table.add_row([task, events.for_task(task).sum()])

        print(formatter(sortby=sort, reversesort=reverse))
    if events.running() and not html:
        current = events.last()
        print(_("Running `%s' since %s")
              % (current.task, isodate.datetime_isoformat(current.start)))


@APP.cmd(help=_("display running task, if any"))
def running(directory):
    """Display running task, if any."""
    events = Events.read(directory)
    if events.running():
        current = events.last()
        print(_('Task %s has been running for %s')
            % (current.task,
               str(utils.utcnow() - current.start).split('.')[0]))
    else:
        print(utils.warn(_('No task is running!')))


@APP.cmd(help=_("display last event, if any"))
def last(directory):
    """Display last event, if any."""
    events = Events.read(directory)
    event = events.last()
    if not events.running():
        print(_('Last task %s, ran for %s') % (event.task, event.delta))
    else:
        print(utils.warn(_('Task %s is still running') % event.task))


@APP.cmd(help=_("generate ledger compatible data file"),
         parents=[duration_parser, task_parser])
@APP.cmd_arg('-r', '--rate', metavar='rate',
             help=_('hourly rate for task output'))
def ledger(directory, task, duration, rate, from_dir):
    """Generate ledger compatible data file."""
    events = filter_events(directory, task, duration)
    if events.running():
        print(_(';; Running event not included in output!'))
    for event in events:
        if not event.delta:
            break
        end = event.start + event.delta
        # Can't use timedelta.total_seconds() as it was only added in 2.7
        seconds = event.delta.days * 86400 + event.delta.seconds
        hours = seconds / 3600.0
        print('%s-%s' % (event.start.strftime('%Y-%m-%d * %H:%M'),
                         end.strftime('%H:%M')))
        print('    (task:%s)  %.2fh%s'
              % (event.task, hours, ' @ %s' % rate if rate else ''))
    if events.running():
        print(_(';; Running event not included in output!'))


def main():
    """Main script."""
    APP.arg('--version', action='version',
            version="%%(prog)s %s" % _version.dotted)
    APP.arg('-d', '--directory', default=utils.xdg_data_location(),
            metavar='dir', help=_('directory to read/write to'))
    try:
        APP.run()
    except utils.RdialError as error:
        print(utils.fail(error.message))
        return 2
