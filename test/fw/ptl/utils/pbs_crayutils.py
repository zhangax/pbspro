# coding: utf-8

# Copyright (C) 1994-2018 Altair Engineering, Inc.
# For more information, contact Altair at www.altair.com.
#
# This file is part of the PBS Professional ("PBS Pro") software.
#
# Open Source License Information:
#
# PBS Pro is free software. You can redistribute it and/or modify it under the
# terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# PBS Pro is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Commercial License Information:
#
# For a copy of the commercial license terms and conditions,
# go to: (http://www.pbspro.com/UserArea/agreement.html)
# or contact the Altair Legal Department.
#
# Altair’s dual-license business model allows companies, individuals, and
# organizations to create proprietary derivative works of PBS Pro and
# distribute them - whether embedded or bundled with other software -
# under a commercial license agreement.
#
# Use of Altair’s trademarks, including but not limited to "PBS™",
# "PBS Professional®", and "PBS Pro™" and Altair’s logos is subject to Altair's
# trademark licensing policies.

import socket
import os

from ptl.utils.pbs_dshutils import DshUtils


class CrayUtils(object):

    """
    Cray specific utility class
    """
    node_status = []
    node_summary = {}
    du = None

    def __init__(self):
        self.du = DshUtils()
        (self.node_status, self.node_summary) = self.parse_apstat_rn()

    def parse_apstat_rn(self):
        """
        Run apstat command on cray/craysim and parse its output

        :param options: options to pass to apstat command
        :type options: str
        :returns: tuple of (node status, node summary)
        """
        status = []
        summary = {}
        count = 0
        options = '-rn'
        hostname = socket.gethostname()
        platform = self.du.get_platform(hostname)
        apstat_env = os.environ
        apstat_cmd = "apstat"
        if 'cray' not in platform:
            return (status, summary)
        if 'craysim' in platform:
            lib_path = '$LD_LIBRARY_PATH:/opt/alps/tester/usr/lib/'
            apstat_env['LD_LIBRARY_PATH'] = lib_path
            apstat_env['ALPS_CONFIG_FILE'] = '/opt/alps/tester/alps.conf'
            apstat_env['apsched_sharedDir'] = '/opt/alps/tester/'
            apstat_cmd = "/opt/alps/tester/usr/bin/apstat -d ."
        cmd_run = self.du.run_cmd(hostname, [apstat_cmd, options],
                                  as_script=True, wait_on_script=True,
                                  env=apstat_env)
        cmd_result = cmd_run['out']
        keys = cmd_result[0].split()
        # Add a key 'Mode' because 'State' is composed of two list items, e.g:
        # State = 'UP  B', where Mode = 'B'
        k2 = ['Mode']
        keys = keys[0:3] + k2 + keys[3:]
        cmd_iter = iter(cmd_result)
        for line in cmd_iter:
            if count == 0:
                count = 1
                continue
            if "Compute node summary" in line:
                summary_line = next(cmd_iter)
                summary_keys = summary_line.split()
                summary_data = next(cmd_iter).split()
                sum_index = 0
                for a in summary_keys:
                    summary[a] = summary_data[sum_index]
                    sum_index += 1
                break
            obj = {}
            line = line.split()
            for i, value in enumerate(line):
                obj[keys[i]] = value
                if keys[i] == 'State':
                    obj[keys[i]] = value + "  " + line[i + 1]
            # If there is no Apids in the apstat then use 'None' as the value
            if "Apids" in obj:
                pass
            else:
                obj["Apids"] = None
            status.append(obj)
        return (status, summary)

    def count_node_summ(self, cnsumm='up'):
        """
        Return the value of any one of the following parameters as shown in
        the 'Compute Node Summary' section of 'apstat -rn' output:
        arch, config, up, resv, use, avail, down

        :param cnsumm: parameter which is being queried, defaults to 'up'
        :type cnsumm: str
        :returns: value of parameter being queried
        """
        return int(self.node_summary[cnsumm])

    def count_node_state(self, state='UP  B'):
        """
        Return how many nodes have a certain 'State' value.

        :param state: parameter which is being queried, defaults to 'UP  B'
        :type state: str
        :returns: count of how many nodes have the state
        """
        count = 0
        status = self.node_status
        for stat in status:
            if stat['State'] == state:
                count += 1
        return count
