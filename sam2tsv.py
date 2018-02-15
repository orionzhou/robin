#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import os.path as op
import sys
import argparse
import pysam

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description = 'Convert SAM file to TSV'
    )
    parser.add_argument(
            'fi', help = 'SAM/BAM file'
    )
    parser.add_argument(
            'fo', help = 'output file (tsv)'
    )
    parser.add_argument(
        '--paired', action = "store_true", help = 'paired end input [No]'
    )
    args = parser.parse_args()
    fi, fo = args.fi, args.fo
    sMatch, sMisMatch, sGapOpen, sGapExtend = 2, -3, -5, -2
    sam = pysam.AlignmentFile(fi, "r")
   
    fho = open(fo, "w")
    fho.write("qId\tqBeg\tqEnd\tqSrd\tqSize\ttId\ttBeg\ttEnd\ttSrd\ttSize\t" +
            "alnLen\tmatch\tmisMatch\tbaseN\tqNumIns\ttNumIns\tqBaseIns\ttBaseIns\tident\tscore\t" +
            "qLoc\ttLoc\n")
    for x in sam.fetch():
        if x.is_unmapped:
            continue
        tId, tBeg, tEnd, tSrd, tSize = x.reference_name, x.reference_start, x.reference_end, "+", x.reference_length
        qId, qBeg, qEnd, qSrd, qSize = x.query_name, x.query_alignment_start, x.query_alignment_end, "+", x.query_length
        tBeg += 1
        qBeg += 1
        if x.is_reverse: qSrd = "-"
        if args.paired:
            if x.is_read2:
                qId += ".2"
            else:
                qId += ".1"
        alnLen, match, misMatch, baseN, qLen = 0,0,0,0,0
        qNumIns, tNumIns, qBaseIns, tBaseIns = 0,0,0,0
        for op, nt in x.cigartuples:
            if op == 0 or op == 7 or op == 8: # M=X
                alnLen += nt
                qLen += nt
            elif op == 1: # I
                qNumIns += 1
                qBaseIns += nt
                qLen += nt
            elif op == 4: # S
                qLen += nt
            elif op == 2 or op == 3: # DN
                tNumIns += 1
                tBaseIns += nt
            elif op == 5:
                print("hard clipping: %s -> %s:%d" % (qId, tId, tBeg))
                exit(1)
        if x.has_tag("NM"):
            misMatch = x.get_tag("NM")
        match = alnLen - misMatch
        if qSize == 0:
            qSize = qLen
        #assert qSize == qEnd, "error qSize: %d > %d" % (qSize, qEnd)
        
        score_match = match * sMatch
        score_misMatch = misMatch * sMisMatch
        numIns = qNumIns + tNumIns
        score_indel = 0
        if numIns >= 1:
            score_indel = sGapOpen + (numIns - 1) * sGapExtend
        score = score_match + score_misMatch + score_indel
        ident = match / (match + misMatch)

        fho.write("%s\t%d\t%d\t%s\t%d\t%s\t%d\t%d\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%.03f\t%d\t%s\t%s\n" % 
                (qId, qBeg, qEnd, qSrd, qSize,
                 tId, tBeg, tEnd, tSrd, tSize,
                 alnLen, match, misMatch, 0,
                 qNumIns, tNumIns, qBaseIns, tBaseIns, ident, score, '', ''))
        #exit(1)
    fho.close()
    