import logging
import os
import shlex
import sys

from chiptools.wrappers.simulator import Simulator
from chiptools.common.filetypes import FileType
from chiptools.common import utils

log = logging.getLogger(__name__)


class Vivado(Simulator):

    name = 'vivado'

    if sys.platform == 'win32':
        platform_suffix = '.bat'
    else:
        platform_suffix = ''

    xvhdl_name = 'xvhdl' + platform_suffix
    xvlog_name = 'xvlog' + platform_suffix
    xelab_name = 'xelab' + platform_suffix
    xsim_name = 'xsim' + platform_suffix

    executables = [xvhdl_name, xvlog_name, xelab_name, xsim_name]

    sim_ini_name = 'xsim.ini'
    sim_tcl_name = 'xsim.tcl'

    def __init__(self, project, user_paths):
        super(Vivado, self).__init__(project, self.executables, user_paths)

        self.xvhdl = os.path.join(self.path, self.xvhdl_name)
        self.xvlog = os.path.join(self.path, self.xvlog_name)
        self.xelab = os.path.join(self.path, self.xelab_name)
        self.xsim = os.path.join(self.path, self.xsim_name)

    def write_includes(self):
        """Write the includes dictionary to the xsim.ini file in the
        simulation directory, which is required by xvlog, xvhdl and xelab
        to locate existing compiled libraries."""
        cwd = self.project.get_simulation_directory()
        with open(os.path.join(cwd, self.sim_ini_name), 'w') as f:
            f.write('--Do not modify this file, any changes will be lost.\n')
            f.write(
                '--Generated by ChipTools on {0}\n'.format(
                    utils.get_date_string()
                )
            )
            for libname, path in self.libraries.items():
                f.write('{0}={1}\n'.format(libname, path))

    def simulate(
        self,
        library,
        entity,
        gui=False,
        generics={},
        includes={},
        args=[],
        duration=None,
    ):
        cwd = self.project.get_simulation_directory()
        # Set simulator generics
        # NOTE: Different behavior is required when calling xelab on Windows
        # as the command line argument to xelab '-generic_top' does not work
        # correctly. See: https://github.com/pabennett/chiptools/issues/1
        if sys.platform == 'win32':
            xelab_args = ''  # use a string sequence for Vivado on Windows
            if gui:
                xelab_args += '-debug all'
            # Add generics
            for name, binding in generics.items():
                # TODO: The -generic_top argument formatting is hacked here for
                # Vivado simulator on Windows. Xilinx may address this issue in
                # the future, which will mean this code needs modifying again.
                # The issue is present in Vivado 2015.4
                xelab_args += (
                    '-generic_top'
                    + ' '
                    + name
                    + '"'
                    + '='
                    + '"'
                    + str(binding)
                    + ' '
                )
            # Add external includes
            for libname, path in includes.items():
                xelab_args += (
                    '-lib' + ' ' + libname + '"' + '=' + '"' + path + ' '
                )
            # Add project libraries
            for libname in self.project.get_libraries():
                xelab_args += (
                    '-lib'
                    + ' '
                    + libname
                    + '"'  # Library Name
                    + '='
                    + '"'
                    + libname
                    + ' '  # Library Path
                )
            # Execute XELAB on the design files:
            xelab_args += ' ' + library + '.' + str(entity)
            xelab_args += ' ' + '-s' + ' ' + str(entity)
            Vivado._call_str_args(self.xelab, xelab_args, cwd=cwd, quiet=False)
        else:
            # Normal behavior on other platforms.
            xelab_args = []
            if gui:
                xelab_args += ['-debug', 'all']
            # Add generics
            for name, binding in generics.items():
                xelab_args += [
                    '-generic_top',
                    name + '=' + str(binding) + ' ',
                ]
            # Add external includes
            for libname, path in includes.items():
                xelab_args += [
                    '-lib',
                    libname + '=' + str(path) + ' ',
                ]
            # Add project libraries
            for libname in self.project.get_libraries():
                xelab_args += [
                    '-lib',
                    libname + '=' + str(libname) + ' ',
                ]

            # Execute XELAB on the design files:
            xelab_args += [library + '.' + str(entity)]
            xelab_args += ['-s', str(entity)]
            Vivado._call(self.xelab, xelab_args, cwd=cwd, quiet=False)
        # Fuse generates a simulation executable, this can be called now with
        # the specified simulator arguments:
        sim_args = []
        if gui:
            sim_args += ['-gui']
            sim_args += ['-onfinish', 'stop']
            sim_args += ['-onerror', 'stop']
        else:
            sim_args += ['-onfinish', 'quit']
            sim_args += ['-onerror', 'quit']
        # Create a TCL file:
        with open(os.path.join(cwd, self.sim_tcl_name), 'w') as f:
            # Set run duration
            if duration is not None:
                if duration <= 0:
                    duration = 'all'
                else:
                    duration = utils.seconds_to_timestring(duration)
                f.write(
                    (
                        'if { [catch {%(command)s} result] } {\n'
                        + '   puts stderr "Command failed: $result"\n'
                        + '   exit 1\n'
                        + '}\n'
                    )
                    % dict(command='run {0}\n'.format(duration))
                )
                f.write('exit\n')
        sim_args += ['-tclbatch', self.sim_tcl_name]
        # Path to snapshot to execute
        sim_args += [entity]
        # Run the simulation
        ret, stdout, stderr = Vivado._call(
            self.xsim,
            sim_args,
            cwd=self.project.get_simulation_directory(),
            quiet=False,
        )

        return ret, stdout, stderr

    def compile(self, file_object, cwd=None):
        cwd = self.project.get_simulation_directory()
        if file_object.library not in self.libraries:
            self.libraries[file_object.library] = file_object.library
        self.write_includes()
        args = self.project.get_tool_arguments(self.name, 'compile')
        if len(args) == 0:
            args = file_object.get_tool_arguments(self.name, 'compile')
        args = shlex.split(['', args][args is not None])
        args += ['-work', file_object.library, file_object.path]
        if file_object.fileType == FileType.VHDL:
            Vivado._call(self.xvhdl, args, cwd=cwd)
        elif file_object.fileType == FileType.Verilog:
            Vivado._call(self.xvlog, args, cwd=cwd)
        elif file_object.fileType == FileType.SystemVerilog:
            Vivado._call(self.xvlog, args, cwd=cwd)
        else:
            log.warning(
                'Vivado wrapper skipping file with unknown type: '
                + file_object.path
            )

    def library_exists(self, libname, workdir):
        if os.path.exists(os.path.join(workdir, libname)):
            return True
        return False

    def set_working_library(self, library, cwd=None):
        pass

    def set_library_path(self, library, path, cwd=None):
        pass

    def add_library(self, library):
        cwd = self.project.get_simulation_directory()
        if not os.path.exists(os.path.join(cwd, library)):
            os.makedirs(os.path.join(cwd, library))
