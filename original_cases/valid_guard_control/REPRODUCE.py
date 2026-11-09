#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Portable analysis-only or complete wireless VALID control reproduction."""
import argparse
import subprocess
import sys
from pathlib import Path
P=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('mode',choices=['analysis','full'])
parser.add_argument('--input',type=Path,help='External raw trace directory (or its parent containing traces/)')
parser.add_argument('--reference-input',type=Path,help='Optional original traces for byte equality')
parser.add_argument('--ns3',type=Path,help='Clean, built ns-3.47 tree; required for full')
parser.add_argument('--work',type=Path,required=True)
args=parser.parse_args(); W=args.work.resolve()
def run(script,*options):
    subprocess.run([sys.executable,str(P/script),*map(str,options)],check=True)
if args.mode=='analysis':
    source=args.input or P/'raw'
    if not source.is_dir():parser.error('Supply --input for the separately distributed scientific traces')
else:
    if args.ns3 is None:parser.error('--ns3 is required for full')
    if args.input is not None:parser.error('Full mode generates its own input; use --reference-input for optional comparison')
    run('build.py','--ns3',args.ns3,'--work',W)
    run('run.py','--ns3',args.ns3,'--work',W)
    source=W/'runs'
options=['--input',source,'--out',W/'analysis']
if args.reference_input is not None:options+=['--reference-input',args.reference_input]
run('analyze.py',*options)
