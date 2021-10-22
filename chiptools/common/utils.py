import subprocess
import os
import logging
import threading
import time
import copy

if __name__ == '__main__':
    import exceptions
else:
    from chiptools.common import exceptions

log = logging.getLogger(__name__)


def subgraph(graph, root):
    """
    Given a graph represented by a dictionary of key (node) and value (set of
    child nodes) and a root node, return a new graph representing the root node
    and its hierarchy.
    >>> graph = {
    ...    2 : set([11]),
    ...    9 : set([11, 8]),
    ...    10 : set([11, 3]),
    ...    11 : set([5, 7]),
    ...    8 : set([7, 3]),
    ...    5 : set(),
    ...    7 : set(),
    ...    3 : set([5])
    ... }
    >>> subgraph(graph, 8)
    {8: {3, 7}, 3: {5}, 5: set(), 7: set()}
    """
    def subgraph_recurse(graph, root, top=False, new_graph=None):
        if top:
            new_graph = {root: graph[root]}
        if root not in new_graph:
            new_graph[root] = set()
        if root not in graph:
            return new_graph
        for child in graph[root]:
            new_graph[root].add(child)
            subgraph_recurse(graph, child, new_graph=new_graph)
        return new_graph
    return subgraph_recurse(graph, root, top=True)


def topological_sort(graph):
    """
    Perform a topological sort on the graph and return a list of sorted nodes.
    The graph is represented as a dictionary where each key is a node and
    the value is a list/set of connected child nodes.
    >>> graph = {
    ...    2 : set([11]),
    ...    9 : set([11, 8]),
    ...    10 : set([11, 3]),
    ...    11 : set([5, 7]),
    ...    8 : set([7, 3]),
    ...    5 : set(),
    ...    7 : set(),
    ...    3 : set()
    ... }
    >>> topological_sort(graph)
    [3, 5, 7, 8, 11, 2, 9, 10]
    """
    # Kahn's Algorithm (https://en.wikipedia.org/wiki/Topological_sorting)
    # L ← Empty list that will contain the sorted elements
    # S ← Set of all nodes with no incoming edges
    # while S is non-empty do
    #     remove a node n from S
    #     add n to tail of L
    #     for each node m with an edge e from n to m do
    #         remove edge e from the graph
    #         if m has no other incoming edges then
    #             insert m into S
    # if graph has edges then
    #     return error (graph has at least one cycle)
    # else
    #     return L (a topologically sorted order
    # Construct a local shallow copy as we directly manipulate graph values
    graph = dict((k, copy.copy(graph[k])) for k in graph.keys())
    l = []
    s = set([node for node in graph if len(graph[node]) == 0])
    while len(s) > 0:
        n = s.pop()
        l.append(n)
        for m in list(filter(lambda x: n in graph[x], graph.keys())):
            graph[m].remove(n)
            if len(graph[m]) == 0:
                s.add(m)
    if any(len(graph[n]) > 0 for n in graph.keys()):
        raise ValueError('Graph contains at least one cycle')
    else:
        return l


def iterate_tests(test_suite_or_case):
    """Iterate through all of the test cases in 'test_suite_or_case'."""
    try:
        suite = iter(test_suite_or_case)
    except TypeError:
        yield test_suite_or_case
    else:
        for test in suite:
            for subtest in iterate_tests(test):
                yield subtest


def get_date_string():
    """
    Return a pretty formatted date string to indicate the time of an event.
    """
    return time.strftime('%d, %b %y at %H:%M:%S')


def parse_range(astr):
    """
    Parse the input string numeric range and return a set of numbers.
    >>> parse_range('1-3, 5, 8, 10')
    [1, 2, 3, 5, 8, 10]
    >>> parse_range('1, 2, 3, 4, 5')
    [1, 2, 3, 4, 5]
    >>> parse_range('1-5, 9-5') # Negative ranges are ignored
    [1, 2, 3, 4, 5]
    """
    result = set()
    for part in astr.split(','):
        x = part.split('-')
        result.update(range(int(x[0]), int(x[-1])+1))
    return sorted(result)


def relative_path_to_abs(path, root=os.getcwd()):
    """
    If the path is relative convert it into an absolute path.  This is the same
    as calling os.path.abspath(path), but with an option to override the
    default root of os.getcwd() and with normalisation and expansion of
    environment variables on the input path.
    """
    path = os.path.normpath(os.path.expandvars(path))
    if not os.path.isabs(path):
        return os.path.normpath(os.path.join(root, path))
    return path


def time_delta_string(start_time, end_time):
    """Return a string representing the time delta in ms
    >>> time_delta_string(50e-3, 100e-3)
    '50.0ms'
    """
    return str(seconds_to_timestring(end_time-start_time))


def seconds_to_timestring(duration):
    """
    Return a formatted time-string for the given duration in seconds.
    Provides auto-rescale/formatting for values down to ns resolution
    >>> seconds_to_timestring(1.0)
    '1.0s'
    >>> seconds_to_timestring(100e-3)
    '100.0ms'
    >>> seconds_to_timestring(500e-6)
    '500.0us'
    >>> seconds_to_timestring(20000.0)
    '20000.0s'
    >>> seconds_to_timestring(453e-9)
    '453.0ns'
    >>> seconds_to_timestring(3000e-9)
    '3.0us'
    >>> seconds_to_timestring(100e-12)
    '0.1ns'
    """
    if duration >= 1000e-3:
        return str(duration) + "s"
    if duration >= 1000e-6:
        return str(duration * 1e3) + "ms"
    if duration >= 1000e-9:
        return str(duration * 1e6) + "us"
    return str(duration * 1e9) + "ns"


def execute(command, path=None, shell=True, quiet=False):
    return popen_throws_ex(command, path, quiet)


def call(command, path=None, shell=True):
    """
    Call the executable in the given path, any messages the program generates
    will be routed to stdout and stderr.
    """
    return_val = 0
    if path:
        return_val = subprocess.call(
            command,
            shell=shell,
            cwd=os.path.expandvars(path)
        )
    else:
        return_val = subprocess.call(command, shell=shell)
    if return_val != 0:
        raise exceptions.ExecutionError(return_val)


def popen_throws_ex(command, path=None, quiet=False):
    """
    Call the executable in the given path, hiding standard output unless the
    return value is an error. If the return value is an error raise an
    exception for the caller to handle.
    """

    if quiet:
        returnVal, stdout, stderr = popen_quiet(command, path)
    else:
        returnVal, stdout, stderr = popen(command, path)

    if returnVal != 0:
        errstring = ''
        if stdout:
            errstring += stdout + '\n'
        if stderr:
            errstring += str(stderr) + '\n'
        raise exceptions.ExecutionError(errstring)

    return returnVal, stdout, stderr


def tee(infile, *files):
    """
    Print `infile` to `files` in a separate thread.
    """
    def fanout(infile, *files):
        while True:
            line = infile.readline().decode('utf-8')
            if line != '':
                for f in files:
                    f.write(line.rstrip() + '\n')  # Normalise line ends
            else:
                break
        infile.close()
    t = threading.Thread(target=fanout, args=(infile,)+files)
    t.daemon = True
    t.start()
    return t


class LogWrapper:
    """Simple class to provide a file interface using a logger
    message function"""
    def __init__(self, logfn):
        self.logfn = logfn

    def write(self, line):
        """Use the logfunction to print the message, strip off any line ends"""
        self.logfn(line.rstrip())


def teed_call(cmd_args, **kwargs):
    stdout, stderr = [kwargs.pop(s, None) for s in ['stdout', 'stderr']]
    p = subprocess.Popen(
        cmd_args,
        stdout=subprocess.PIPE if stdout is not None else None,
        stderr=subprocess.PIPE if stderr is not None else None,
        **kwargs
    )
    threads = []
    if stdout is not None:
        threads.append(tee(p.stdout, stdout, LogWrapper(log.info)))
    if stderr is not None:
        threads.append(tee(p.stderr, stderr, LogWrapper(log.error)))
    for t in threads:
        t.join()  # wait for IO completion
    return p.wait()


def popen(command, path=None):
    from io import StringIO
    fout, ferr = StringIO(), StringIO()
    exitcode = teed_call(command, cwd=path, stdout=fout, stderr=ferr)
    stdout = fout.getvalue()
    stderr = ferr.getvalue()
    return exitcode, stdout, stderr


def popen_quiet(command, path=None):
    """
    Call the executable in the given path and return the standard output and
    error streams.
    """
    returnVal = 0
    stdout = ''
    stderr = ''
    if path:
        process = subprocess.Popen(
            command,
            cwd=path,
            stdout=subprocess.PIPE
        )
        # execute it, get stdout and stderr
        stdout, stderr = process.communicate()
        # when finished, get the exit code
        returnVal = process.wait()
    else:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE
        )
        # execute it, get stdout and stderr
        stdout, stderr = process.communicate()
        # when finished, get the exit code
        returnVal = process.wait()

    if stdout:
        stdout = stdout.decode('utf-8')
    if stderr:
        stderr = stderr.decode('utf-8')

    return returnVal, stdout, stderr

if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=True)
