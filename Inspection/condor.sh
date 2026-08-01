#!/bin/bash
#######################################################################################

#ClusterId= $1
#ProcId=    $2
#Comment=   $3
#runnumber= $4

#######################################################################################

source /cvmfs/ship.cern.ch/26.04/setUp.sh #/cvmfs/ship.cern.ch/24.10/setUp.sh 
source /afs/cern.ch/work/j/jaweiss/private/HTCondor_scripts/config_26.04.sh #alienv load FairShip/latest-master-release > config_<version>.sh
echo 'environment set'
#######################################################################################

python /afs/cern.ch/work/j/jaweiss/private/MuonBack/Inspection/inspect_Back.py --path /eos/user/j/jaweiss/MuonBack/TRY2PlSc --tag TRY2PlSc
