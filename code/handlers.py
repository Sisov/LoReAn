#!/usr/bin/env python3

import dirsAndFiles as logistic
import multithreadLargeFasta as multiple
import transcriptAssembly as transcripts


def braker_aat(queue, ref, bamFile, species_name, protein_evidence, threads, fungus, list_fasta_names, wd, braker_out, verbose):
    '''Handles Braker and AAT so that we can run them in parallel'''
    # DIVIDE THREADS BY 2
    use = (round(int(threads) / 2) - 1)
    aat_wd = wd + 'AAT/'
    logistic.check_create_dir(aat_wd)
    while True:
        dummy = queue.get()
        if dummy == 0:
            transcripts.braker_call(braker_out, ref, bamFile, species_name, use, fungus, verbose)
        if dummy == 1:
            multiple.aat_multi(use, protein_evidence, list_fasta_names, aat_wd, verbose)
        queue.task_done()


def august_gmes_aat(queue, ref, species, protein_evidence, threads, fungus, list_fasta_names, wd, verbose):
    use = (round(int(threads) / 3)-1)
    use_gmes = str(use)
    augustus_wd = wd + 'augustus/'
    logistic.check_create_dir(augustus_wd)
    gmes_wd = wd + 'gmes/'
    logistic.check_create_dir(gmes_wd)
    aat_wd = wd + 'AAT/'
    logistic.check_create_dir(aat_wd)
    while True:
        dummy = queue.get()
        if dummy == 0:
            multiple.augustus_multi(use, species, list_fasta_names, augustus_wd, verbose)
        if dummy == 1:
            multiple.aat_multi(use, protein_evidence, list_fasta_names, aat_wd, verbose)
        if dummy == 2:
            transcripts.gmes_call(gmes_wd, ref, fungus, use_gmes, verbose)
        queue.task_done()

