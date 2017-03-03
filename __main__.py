import time

from nbformat import read
from runipy.notebook_runner import NotebookRunner
from steemdata.helpers import timeit


def run_notebook(filename='Charts'):
    """ Run Specific Notebook. """
    # convert to v3 of notebook format, as v4 is not supported yet
    notebook = read(open('%s.ipynb' % filename), 3)
    r = NotebookRunner(notebook)
    r.run_notebook()


def run():
    """ Run a chart updating notebook twice a day. """
    while True:
        print('Running Charts notebook...')
        with timeit():
            run_notebook()
        print('Done.')
        time.sleep(3600 * 12)


if __name__ == '__main__':
    run()
