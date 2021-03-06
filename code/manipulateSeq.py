#!/usr/bin/env python3
import ctypes as ct
import datetime
import os
import subprocess
import sys
from Bio import SeqIO
from Bio.Seq import reverse_complement
from multiprocessing import Pool

import ssw_lib


def to_int(seq, lEle, dEle2Int):
    """
    it is used for the alignment of the primers to the reads
    :param seq: 
    :param lEle: 
    :param dEle2Int: 
    :return: 
    """
    num_decl = len(seq) * ct.c_int8
    num = num_decl()
    for i,ele in enumerate(seq):
        try:
            n = dEle2Int[ele]
        except KeyError:
            n = dEle2Int[lEle[-1]]
        finally:
            num[i] = n
    return num


def align_one(ssw, qProfile, rNum, nRLen, nOpen, nExt, nFlag, nMaskLen):
    """
    this function calculate the score and other results from the alignment
    """
    res = ssw.ssw_align(qProfile, rNum, ct.c_int32(nRLen), nOpen, nExt, nFlag, 0, 0, int(nMaskLen))
    nScore = res.contents.nScore
    nScore2 = res.contents.nScore2
    nRefBeg = res.contents.nRefBeg
    nRefEnd = res.contents.nRefEnd
    nQryBeg = res.contents.nQryBeg
    nQryEnd = res.contents.nQryEnd
    nRefEnd2 = res.contents.nRefEnd2
    lCigar = [res.contents.sCigar[idx] for idx in range(res.contents.nCigarLen)]
    nCigarLen = res.contents.nCigarLen
    ssw.align_destroy(res)
    return nScore, nScore2, nRefBeg, nRefEnd, nQryBeg, nQryEnd, nRefEnd2, nCigarLen, lCigar


def align_call(elem):
    """
    this function call the aligner software
    :param elem: 
    :return: 
    """
    record = elem[0]
    adapter = elem[1]
    lEle = []
    dRc = {} 
    dEle2Int = {}
    dInt2Ele = {}
    nMatch = 2
    nMismatch = 1
    nOpen = 1
    nExt = -2
    nFlag = 0
    #if not args.sMatrix:
    lEle = ['A', 'C', 'G', 'T', 'N']
    for i,ele in enumerate(lEle):
        dEle2Int[ele] = i
        dEle2Int[ele.lower()] = i
        dInt2Ele[i] = ele
    nEleNum = len(lEle)
    lScore = [0 for i in range(nEleNum**2)]
    for i in range(nEleNum-1):
        for j in range(nEleNum-1):
            if lEle[i] == lEle[j]:
                lScore[i*nEleNum+j] = nMatch
            else:
                lScore[i*nEleNum+j] = -nMismatch
    mat = (len(lScore) * ct.c_int8) ()
    mat[:] = lScore
    
    ssw = ssw_lib.CSsw("./")
    sQSeq = record.seq
    sQId = record.id
    if len(sQSeq) > 30:
        nMaskLen = len(sQSeq) / 2
    else:
        nMaskLen = 15
    outputAlign = []
    qNum = to_int(sQSeq, lEle, dEle2Int)
    qProfile = ssw.ssw_init(qNum, ct.c_int32(len(sQSeq)), mat, len(lEle), 2)
    sQRcSeq = reverse_complement(sQSeq)
    qRcNum = to_int(sQRcSeq, lEle, dEle2Int)
    qRcProfile = ssw.ssw_init(qRcNum, ct.c_int32(len(sQSeq)), mat, len(lEle), 2)
    sRSeq = adapter.seq
    sRId = adapter.id
    rNum = to_int(sRSeq, lEle, dEle2Int)
    res = align_one(ssw, qProfile, rNum, len(sRSeq), nOpen, nExt, nFlag, nMaskLen)
    resRc = None
    resRc = align_one(ssw, qRcProfile, rNum, len(sRSeq), nOpen, nExt, nFlag, nMaskLen)
    strand = 0
    if res[0] == resRc[0]:
        next
    if res[0] > resRc[0]:
        res = res
        strand = 0
        outputAlign = [sRId , sQId, strand, res]
    elif res[0] < resRc[0]:
        res = resRc
        strand = 1
        outputAlign = [sRId , sQId, strand, res]
    ssw.init_destroy(qProfile)
    ssw.init_destroy(qRcProfile)
    return outputAlign


def filterLongReads(fastq_filename, min_length, max_length, wd, adapter, threads, a):
    """
    Filters out reads longer than length provided and it is used to call the alignemnt and parse the outputs
    """
    seq_dict = {}
    first_dict_score = {}
    first_dict_seq = {}
    score_dict = {}
    listA_adapter = []
    final_seq = []
    list_seq_adap = []
    record_dict = {}
    max_score = 0
    if a and not adapter:
        out_filename = wd + fastq_filename + '.longreads.filtered.fasta'
    elif a and adapter:
        out_filename = wd + fastq_filename + '.longreads.filtered.oriented.fasta'
    else:
        out_filename = fastq_filename + '.longreads.filtered.fasta'
    filter_count = 0
    if os.path.isfile(out_filename):
            sys.stdout.write(('Filtered FASTQ existed already: ' + out_filename + ' --- skipping\n'))
            return out_filename, 0
    if fastq_filename.endswith('fastq') or fastq_filename.endswith('fq'):
        for record in SeqIO.parse(fastq_filename, "fastq"):
            if len(str(record.seq)) > int(min_length) < int(max_length):
                record.description= ""
                record.name = ""
                record.id = str(filter_count)
                filter_count += 1
                record_dict[record.id] = record
    elif fastq_filename.endswith('fasta') or fastq_filename.endswith('fa'):
        for record in SeqIO.parse(fastq_filename, "fasta"):
            if int(min_length) < len(str(record.seq)) < int(max_length):
                record.description= ""
                record.name = ""
                record.id = str(filter_count)
                filter_count += 1
                record_dict[record.id] = record
    if adapter:
        for adpt in SeqIO.parse(adapter, "fasta"):
            listA_adapter.append(adpt.id)
            list_seq_adap.append(adpt)
    outFile = open(out_filename, 'w')

    filter_count = 0
    if len(listA_adapter) == 1:
        filter_count = 0
        list_command = []
        for key in record_dict:
            for adpter in list_seq_adap:
                list_command.append([record_dict[key], adpter])
        with Pool(processes=int(threads), maxtasksperchild=1000) as p:
            align_resul = p.map(align_call, list_command, chunksize=1)
        for aling_res in align_resul:
            if len(aling_res) == 0:
                next
            else:
                seq_dict[aling_res[1]] = [record_dict[aling_res[1]], aling_res[2]]
                score_dict[aling_res[1]] =  aling_res[3]
        numbers = [score_dict[key][0] for key in score_dict]
        value_optimal = float(sum(numbers)) / max(len(numbers), 1)
        #for key in score_dict:

        #    if score_dict[key][0] > max_score:
        #        max_score = score_dict[key][0]
        #value_optimal = max_score - (max_score/20)
        for key in score_dict:
            if score_dict[key][0] > value_optimal and seq_dict[key][1] == 0:
                filter_count += 1
                final_seq.append(seq_dict[key][0])
            elif score_dict[key][0]  > value_optimal and seq_dict[key][1] == 1:
                filter_count += 1
                sequenze = reverse_complement(seq_dict[key][0].seq)
                seq_dict[key][0].seq = sequenze
                final_seq.append(seq_dict[key][0])
    elif len(listA_adapter) == 2:
        filter_count = 0
        list_command = []
        for key in record_dict:
            for adpter in list_seq_adap:
                list_command.append([record_dict[key], adpter])
        with Pool(processes=int(threads), maxtasksperchild=1000) as p:
            align_resul = p.map(align_call, list_command, chunksize=1)
        for aling_res in align_resul:
            if len(aling_res) == 0:
                next
            elif aling_res[1] in first_dict_seq:
                seq_dict[aling_res[1]] =  first_dict_seq[aling_res[1]]  +  [ aling_res[2], aling_res[0]]
                score_dict[aling_res[1]] = first_dict_score[aling_res[1]]  +  [ aling_res[0], aling_res[3]]
            else:
                first_dict_seq[aling_res[1]] = [record_dict[aling_res[1]], aling_res[2], aling_res[0]]
                first_dict_score[aling_res[1]] =  [ aling_res[0], aling_res[3]]
        max_score_first = 0
        max_score_second = 0
        for key in score_dict:
            score = score_dict[key]
            if score[0] == listA_adapter[0] and score[1][0] > max_score_first:
                max_score_first = score[1][0]
            if score[2] == listA_adapter[0] and score[3][0] > max_score_first:
                max_score_first = score[3][0]
            if score[0] == listA_adapter[1] and score[1][0] > max_score_second:
                max_score_second = score[1][0]
            if score[2] == listA_adapter[1] and score[3][0] > max_score_second:
                max_score_second = score[3][0]
        value_optimal_first = max_score_first - (max_score_first/30)
        value_optimal_second = max_score_second - (max_score_second/30)
        listReadsOverLimit = []
        for key in score_dict:
            score = score_dict[key]
            if (score[0] == listA_adapter[0] and score[1][0] > value_optimal_first) and (score[2] == listA_adapter[1] and score[3][0] > value_optimal_second):
                listReadsOverLimit.append(key)
            elif (score[2] == listA_adapter[0] and score[3][0] > value_optimal_first) and (score[0] == listA_adapter[1] and score[1][0] > value_optimal_second):
                listReadsOverLimit.append(key)
        for key in listReadsOverLimit:
            if seq_dict[key][1] == 1 and seq_dict[key][3] == 0:
                if seq_dict[key][2] == listA_adapter[0] and seq_dict[key][4] == listA_adapter[1]:
                    final_seq.append(seq_dict[key][0])
                elif seq_dict[key][2] in listA_adapter[1] and seq_dict[key][4] in listA_adapter[0]:
                    sequenze = reverse_complement(seq_dict[key][0].seq)
                    seq_dict[key][0].seq = sequenze
                    final_seq.append(seq_dict[key][0])
            elif seq_dict[key][1] == 0 and seq_dict[key][3] == 1:
                if seq_dict[key][2] == listA_adapter[0] and seq_dict[key][4] == listA_adapter[1]:
                    sequenze = reverse_complement(seq_dict[key][0].seq)
                    seq_dict[key][0].seq = sequenze
                    final_seq.append(seq_dict[key][0])
                elif seq_dict[key][2] in listA_adapter[1] and seq_dict[key][4] in listA_adapter[0]:
                    final_seq.append(seq_dict[key][0])
    elif len(listA_adapter) == 0:
        for key in record_dict:
            if int(min_length) < len(str(record_dict[key].seq)) < int(max_length):
                filter_count += 1
                final_seq.append(record_dict[key])
    SeqIO.write(final_seq, out_filename, "fasta")

    fmtdate = '%H:%M:%S %d-%m'
    now = datetime.datetime.now().strftime(fmtdate)

    sys.stdout.write(("###FINISHED FILTERING AT:\t" + now +
                      "###\n\n###LOREAN KEPT\t\033[32m" + str(filter_count) + "\033[0m\tREADS AFTER LENGTH FILTERING###\n"))

    return out_filename


def maskedgenome(wd, ref , gff3):
    """
    this module is used to mask the genome when a gff or bed file is provided
    """

    if '/' in ref:
        out_name = wd + "/" +  ref.split('/')[-1] + '.masked.fasta'
    else:
        out_name = wd + "/" +  ref + '.masked.fasta'
    outmerged = wd + "/" + gff3 + '.masked.gff3'
    outputmerge = open(outmerged, 'w')
    cat = subprocess.Popen(['cat', gff3], stdout = subprocess.PIPE)
    bedsort = subprocess.Popen(['bedtools', 'sort'], stdin = cat.stdout, stdout = subprocess.PIPE)
    bedmerge = subprocess.Popen(['bedtools', 'merge'], stdout = outputmerge, stdin = bedsort.stdout)
    bedmerge.communicate()
    outputmerge.close()
    maskfasta = subprocess.Popen(['bedtools', 'maskfasta', '-fi', ref , '-bed', outmerged, '-fo', out_name])
    maskfasta.communicate()
    return out_name