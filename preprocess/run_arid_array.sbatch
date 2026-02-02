#!/bin/bash
#SBATCH --job-name=ARID_proc
#SBATCH --account=cwp162
#SBATCH --partition=shared-128     
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --mail-type=ALL # Type of email notification- BEGIN,END,FAIL,ALL
#SBATCH --mail-user=dnash@ucsd.edu # Email to which notifications will be sent
#SBATCH --array=0-100                  # adjust after counting ARIDs

#SBATCH --output=logs/arid_%A_%a.out
#SBATCH --error=logs/arid_%A_%a.err

# --- environment ---
source /home/dnash/miniconda3/envs/SEAK-impacts/etc/conda/activate.d/*

# --- run ---
/home/dnash/miniconda3/envs/SEAK-impacts/bin/python -u process_arids.py
