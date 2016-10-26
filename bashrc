#!/bin/bash
#
# bashrc
#
# Set up development environment


# Root directory of the project, the directory in which this script resides
# Recall that "$BASH_SOURCE" is the relative path of a sourced script
export PROJECT_HOME=`cd $(dirname "${BASH_SOURCE}") && pwd -P`

# Make sure virtual environment has been set up
VENV_DIR="${PROJECT_HOME}/.venv"
if [ ! -d "${VENV_DIR}" ]; then
  echo "Error: can't find virtualenv directory ${VENV_DIR}"
  echo "HINT: virtualenv -p python3 ${VENV_DIR}"
  echo "HINT: pip install -r requirements.txt"
  return 1
fi

# Activate virtual environment
source ${VENV_DIR}/bin/activate

# Add libraries to Python search path
export PYTHONPATH="${PROJECT_HOME}/mailmerge:${PYTHONPATH}"

# Add tools to shell search path
export PATH="${PROJECT_HOME}/bin:${PATH}"

# Verbose debugging when submitting to PyPI
export DISTUTILS_DEBUG="true"
