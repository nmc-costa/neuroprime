#!/bin/sh
#activate env 
#1.If main environment has pyff deppendencies
#previous to conda 4.6 : source activate neuroprime
conda activate neuroprime
#2.If not Create a pyff environment
#source activate pyffEV

# Force sign a python binary to avoid OSX firewall nagging
sudo codesign --force --deep --sign - $(which python)

# GET PATHs
script_path="${BASH_SOURCE[0]}";
#echo "srcipt_p=[${script_path}]"
batchs_path="$(dirname "$script_path")"
echo "batchs_path=[${batchs_path}]"
src_path="$(dirname "$batchs_path")"
echo "src_path=[${src_path}]"
feedbackapps_p=""${src_path}"/signal_presentation/feedbackapps"
maincode_p="$(dirname "$src_path")"
pyff_p=""${maincode_p}"/modules/pyff/src"
echo "pyff_p=[${pyff_p}]"

#change cwd for pyff
cd ${pyff_p}

#start pyff
python FeedbackController.py --protocol=json --additional-feedback-path="${feedbackapps_p}"
