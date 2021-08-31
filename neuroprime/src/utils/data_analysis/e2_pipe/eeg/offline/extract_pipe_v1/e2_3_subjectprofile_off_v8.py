#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 14:51:34 2020

@author: nm.costa
"""
from __future__ import (absolute_import, division, print_function)
from builtins import *  # all the standard builtins python 3 style

import os
import pandas as pd
import copy
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.info('Logger started')
logger.setLevel(logging.INFO)
# My functions
#import neuroprime.src.utils.myfunctions as my


def df_to_excel(DataFrame, filedir, filename):
    logger.warning("TRYING TO SAVE...")
    writer = pd.ExcelWriter(os.path.join(filedir, filename) + '.xlsx')
    DataFrame.to_excel(writer, 'Sheet1')
    writer.save()


def recreate_column_names(df):
    for col in df.columns:
        cell = col
        cell_sub = cell
        if cell_sub.find('_positive_response') > -1:
            cell_sub = cell_sub.replace(
                '_positive_response', '_+')  # replace if it exists
        if cell_sub.find('_negative_response') > -1:
            cell_sub = cell_sub.replace(
                '_negative_response', '_-')  # replace if it exists
        if cell_sub.find('_non_responders') > -1:
            cell_sub = cell_sub.replace(
                '_non_responders', '_non')  # replace if it exists
        if cell_sub.find('_breathing_') > -1:
            cell_sub = cell_sub.replace(
                '_breathing_', '_b_')  # replace if it exists
        if cell_sub.find('_imagery_') > -1:
            cell_sub = cell_sub.replace(
                '_imagery_', '_i_')  # replace if it exists
        if cell_sub.find('EXCLUDED_SUBJECTS') > -1:
            cell_sub = cell_sub.replace(
                'EXCLUDED_SUBJECTS', 'EX_SUB')  # replace if it exists
        if cell_sub.find('EXCLUDED_TASKS') > -1:
            cell_sub = cell_sub.replace(
                'EXCLUDED_TASKS', 'EX_TASK')  # replace if it exists
        df = df.rename(columns={cell: cell_sub})
    return df


def get_profile_df_extend(profile_df, profile_df_extend):
    for col in profile_df.columns:
        for idx in profile_df.index:
            # subject cell list; df[col][row] chaining indexing gets a copy of
            # the cell not the cell object
            subject_l = profile_df[col][idx]
            for s in subject_l:
                p_eyes = idx.split('_')[-1]
                col_ext = p_eyes + '_' + col
                idx_ext = profile_df_extend.index[
                    profile_df_extend['subject'] == s[0]]
                # df[col][row] chaining indexing fails, use df.at[row,col];
                # https://kanoki.org/2019/04/12/pandas-how-to-get-a-cell-value-and-update-it/
                profile_df_extend.at[idx_ext, col_ext] = 1
    return profile_df_extend


def get_profile_df(profile_df, filedir, group="CG", subject="S002", band="alpha", feat="ratio_power_threshold", high_feat_rule=1.5, low_feat_rule=0.5, exclude_rule_epoch=40, exclude_rule_protocol="exclude_protocol", task_reference_ec=["rest_ec_1"], task_reference_eo=["rest_eo_2"], task_target_ec=["alpha_ec_9", "alpha_ec_11"], task_target_eo=["alpha_eo_14"]):
    # GET task_bands_df
    task_bands_df = pd.read_pickle(os.path.join(
        filedir, group + "_" + subject + "_" + band + "_" + "tasks_df" + ".pcl"))

    # GET FEAT REFERENCE TO CLASSIFY RESPONSE (for ec and eo)
    feat_reference_ec = task_bands_df.loc[task_bands_df[
        'fileid'] == task_reference_ec[0]][feat].values[0]
    feat_reference_eo = task_bands_df.loc[task_bands_df[
        'fileid'] == task_reference_eo[0]][feat].values[0]

    # Exclude rule
    # exclude_protocol - exclude only eyes open or eyes close;
    # #exclude_subject - if one of the protocols is bad exclude all
    exclude_rule_protocol = exclude_rule_protocol
    exclude_eo = False
    exclude_ec = False

    # loop through all the tasks
    for row_idx in task_bands_df.index:
        feat_value = task_bands_df[feat][row_idx]
        task_type = task_bands_df["task"][row_idx]
        total_epoch_nr = task_bands_df["total_epochs"][row_idx]
        fid = task_bands_df["fileid"][row_idx]
        split_fid = fid.split('_')
        task_name = split_fid[0].lower()  # make every name lower
        protocol = split_fid[1]  # ec or eo
        task_nr = split_fid[2]
        # WARNING: only letting the first problmatic task to be the motif of
        # exclusion
        if protocol == "eo" and exclude_eo:
            continue
        if protocol == "ec" and exclude_ec:
            continue

        # EXCLUDE SUBJECTS based on rules before construction of profile_df
        motif = None
        exclude_subject = [False, motif]
        # 1-epoch rule
        motif = "total_epoch_" + \
            str(total_epoch_nr) + "_below_" + \
            str(exclude_rule_epoch) + "percent"
        # task for target outcome
        if fid in task_target_ec + task_target_eo:
            if (total_epoch_nr / 180.0) * 100 < exclude_rule_epoch:
                exclude_subject = [True, motif]
                col = 'EXCLUDED_SUBJECTS'
                r = group + "_" + protocol
                value = fid + '_' + exclude_subject[1]  # motif
                profile_df[col][r].append([subject, value])
                if exclude_rule_protocol == "exclude_subject":
                    r = group + "_" + 'ec'
                    if protocol == "eo":
                        r = group + "_" + 'eo'
                    # add to other protocol
                    profile_df[col][r].append([subject, value])
                    return profile_df  # return subject
                if protocol == "eo":
                    exclude_eo = True
                if protocol == "ec":
                    exclude_ec = True
        # task for Reference
        if fid in task_reference_ec + task_reference_eo:
            if task_nr == "1" or task_nr == "2" or task_nr == "12" or task_nr == "13":
                if (total_epoch_nr / 90.0) * 100 < exclude_rule_epoch:  # 90s=90epochs
                    exclude_subject = [True, motif]
                    col = 'EXCLUDED_SUBJECTS'
                    r = group + "_" + protocol
                    value = fid + '_' + exclude_subject[1]  # motif
                    profile_df[col][r].append([subject, value])
                    if exclude_rule_protocol == "exclude_subject":
                        r = group + "_" + 'ec'
                        if protocol == "eo":
                            r = group + "_" + 'eo'
                        # add to other protocol
                        profile_df[col][r].append([subject, value])
                        return profile_df  # return subject
                    if protocol == "eo":
                        exclude_eo = True
                    if protocol == "ec":
                        exclude_ec = True
            else:
                if (total_epoch_nr / 180.0) * 100 < exclude_rule_epoch:  # 180s=180epochs
                    exclude_subject = [True, motif]
                    col = 'EXCLUDED_SUBJECTS'
                    r = group + "_" + protocol
                    value = fid + '_' + exclude_subject[1]  # motif
                    profile_df[col][r].append([subject, value])
                    if exclude_rule_protocol == "exclude_subject":
                        r = group + "_" + 'ec'
                        if protocol == "eo":
                            r = group + "_" + 'eo'
                        # add to other protocol
                        profile_df[col][r].append([subject, value])
                        return profile_df  # return subject
                    if protocol == "eo":
                        exclude_eo = True
                    if protocol == "ec":
                        exclude_ec = True

        # CONSTRUCTION of profile_df
        # If the protocol was exluded in this task, go to next task
        if protocol == "eo" and exclude_eo:
            continue
        if protocol == "ec" and exclude_ec:
            continue
        #assert feat_reference
        feat_reference = None
        if protocol == "ec":
            feat_reference = feat_reference_ec
        if protocol == "eo":
            feat_reference = feat_reference_eo
        if not feat_reference:
            raise RuntimeError("Problems in the feature reference!")
        # EXCLUDE TASKS based on same rules for excluding subjects
        motif = None
        exclude_task = [False, motif]
        # 1-Exclude epoch rule
        motif = "total_epoch_" + \
            str(total_epoch_nr) + "_below_" + \
            str(exclude_rule_epoch) + "percent"
        if task_type == "NFT":  # choose NFT to check response
            if (total_epoch_nr / 180.0) * 100 < exclude_rule_epoch:
                exclude_task = [True, motif]
        if task_type == "REST":
            if task_nr == "1" or task_nr == "2" or task_nr == "12" or task_nr == "13":
                if (total_epoch_nr / 90.0) * 100 < exclude_rule_epoch:
                    exclude_task = [True, motif]
            else:
                if (total_epoch_nr / 180.0) * 100 < exclude_rule_epoch:
                    exclude_task = [True, motif]
        if task_type == "PRIME":
            if (total_epoch_nr / 180.0) * 100 < exclude_rule_epoch:
                exclude_task = [True, motif]

        # RESPONSE rule (each group)
        response = "non_responders"
        feat_ratio = round(feat_value / feat_reference, 2)
        if feat_ratio > high_feat_rule:
            response = "positive_response"  # change feat_value/feat_reference
        if feat_ratio < low_feat_rule:
            response = "negative_response"

        # TASK rules
        value = feat_ratio
        if task_type == "NFT":  # choose NFT to check response
            if (task_nr == "9" and protocol == "ec") or (task_nr == "11" and protocol == "ec") or (task_nr == "14" and protocol == "eo"):  # choosing last NFTs
                col = task_type + '_' + response
                r = group + "_" + protocol
                if exclude_task[0]:
                    col = 'EXCLUDED_TASKS'
                    value = fid + '_' + exclude_task[1]  # motif
                profile_df[col][r].append([subject, value])

        if task_type == "REST":
            if task_nr == "12" or task_nr == "13":  # get last Rest for eo and ec
                col = task_type + '_' + response
                r = group + "_" + protocol
                if exclude_task[0]:
                    col = 'EXCLUDED_TASKS'
                    value = fid + '_' + exclude_task[1]  # motif
                profile_df[col][r].append([subject, value])

        if task_type == "PRIME":  # get all the primes
            if task_name.find("image") > -1:
                task_name = "imagery"
            if task_name.find("breath") > -1:
                task_name = "breathing"
            col = task_type + '_' + task_name + '_' + response
            r = group + "_" + protocol
            if exclude_task[0]:
                col = 'EXCLUDED_TASKS'
                value = fid + '_' + exclude_task[1]  # motif
            profile_df[col][r].append([subject, value])

    return profile_df


def play_subject_profile(datadir, outdir, band="alpha", studyname="test_1"):
    #---DATA DIR
    # '/Users/nm.costa/Google_Drive/projects/phd/research/2_THESIS_PUBLICATIONS/thesis/C3_e2_results/results/eeg/e2_study_1_pz_avgref' #'/Volumes/Seagate/e2_priming/e2_data_da_pz_avgref' #my.get_test_folder(foldername="e2_data")#
    datadir = datadir
    # outdir
    outdir = outdir  # my.get_test_folder(foldername="e2_profile_study")#

    # band
    band = band  # "alpha"

    # study name
    studyname = studyname  # band+"_"+"test_1_ratio_power_threshold"

    # feature & Response rule
    # "absolute_power"="ratio_power_threshold";'tBAT';'tonic_increase';
    feat = "ratio_power_threshold"
    high_feat_rule = 1.3  # >positive response
    low_feat_rule = 0.7  # <negative response

    # Exclude subjects & tasks rule
    exclude_rule_epoch = 40  # % exclude tasks and subjects based on this rule; basically on NFT will be motive of subject exclusion; while on the other tasks motive of task_exclusion
    # Exclude protocol rule
    # exclude_protocol - exclude only eyes open or eyes close;
    # #exclude_subject - if one of the protocols is bad exclude all
    exclude_rule_protocol = "exclude_protocol"

    # Tasks for Feature baseline reference
    task_reference_ec = ["rest_ec_1"]
    task_reference_eo = ["rest_eo_2"]
    # Tasks for Feature Target outcome (important for exclusion subject
    # criteria)
    task_target_ec = ["alpha_ec_9", "alpha_ec_11"]
    task_target_eo = ["alpha_eo_14"]

    # bad subjects list
    exclude_subjects_l = ['S063', 'S064', 'S065']
    append_exclude_subjects_l = False  # append to profile this excluded channels
#    for i in range(38,64):
#        exclude_subjects_l.append('S'+ '{num:03d}'.format(num=i))

    # study profile init dataframes
    index_rows = ["EG_eo", "CG_eo", "EG_ec", "CG_ec"]
    columns = ['NFT_positive_response', 'NFT_negative_response',
               'NFT_non_responders', 'REST_positive_response',
               'REST_negative_response', 'REST_non_responders',
               'PRIME_breathing_positive_response',
               'PRIME_breathing_negative_response',
               'PRIME_breathing_non_responders',
               'PRIME_imagery_positive_response',
               'PRIME_imagery_negative_response',
               'PRIME_imagery_non_responders',
               'EXCLUDED_SUBJECTS',
               'EXCLUDED_TASKS']
    profile_df = pd.DataFrame(index=index_rows, columns=columns)
    profile_df_nr = copy.deepcopy(profile_df)
    for col in profile_df.columns:  # define cells as lists for profile_df
        profile_df[col] = [[] for idx in profile_df.index]
    for col in profile_df_nr.columns:  # define cells as zeros for profile_df
        profile_df_nr[col] = [0 for idx in profile_df_nr.index]
    # profile df extended by subject code
    column_eo = []
    column_ec = []
    for c in columns:
        column_eo.append('eo_' + c)
        column_ec.append('ec_' + c)
    columns_extend = ['subject'] + column_eo + column_ec
    profile_df_extend = pd.DataFrame(columns=columns_extend)

    # GET PROFILE : Factorial design folder analysis
    groupdir = datadir
    group_l = os.listdir(groupdir)
    for g in group_l:
        subjectdir = os.path.join(groupdir, g)
        if not os.path.isdir(subjectdir):
            continue  # test if is a folder
        subject_l = os.listdir(subjectdir)
        subject_l.sort()  # sort subjects correctly
        for s in subject_l:
            filedir = os.path.join(subjectdir, s)
            if not os.path.isdir(filedir):
                continue  # test if is a folder
            if exclude_subjects_l and s in exclude_subjects_l:
                if append_exclude_subjects_l:
                    col = 'EXCLUDED_SUBJECTS'
                    r = g + "_" + "eo"
                    profile_df[col][r].append([s, "excluded_subjects_l"])
                    r = g + "_" + "ec"
                    profile_df[col][r].append([s, "excluded_subjects_l"])
                    profile_df_extend = profile_df_extend.append(
                        {'subject': s}, ignore_index=True)  # adding subjects to extend
                continue
            profile_df_extend = profile_df_extend.append(
                {'subject': s}, ignore_index=True)  # adding subjects to extend
            logger.info('\n>> GETTING PROFILE FROM:  {}, {}'.format(g, s))
            #****get_profile_df (for all file dirs)******
            try:
                profile_df = get_profile_df(profile_df, filedir, group=g, subject=s, band=band, feat=feat, high_feat_rule=high_feat_rule, low_feat_rule=low_feat_rule, exclude_rule_epoch=exclude_rule_epoch,
                                            exclude_rule_protocol=exclude_rule_protocol, task_reference_ec=task_reference_ec, task_reference_eo=task_reference_eo, task_target_ec=task_target_ec, task_target_eo=task_target_eo)
            except Exception as e:
                logger.error("\n>> ERROR in {}; \n>> MESSAGE: {}".format(s, e))
                col = 'EXCLUDED_SUBJECTS'
                r = g + "_" + "eo"
                profile_df[col][r].append([s, "missing_file_error"])
                r = g + "_" + "ec"
                profile_df[col][r].append([s, "missing_file_error"])
                pass

    # create profile numbers
    for col in profile_df.columns:
        for idx in profile_df.index:
            profile_df_nr[col][idx] = len(profile_df[col][idx])

    # create profile  extended
    # define cells as zeros (zero is not belonging)
    for col in profile_df_extend.columns:
        if col == "subject":
            continue  # jump this col
        profile_df_extend[col] = [0 for idx in profile_df_extend.index]
    profile_df_extend = get_profile_df_extend(profile_df, profile_df_extend)
    profile_df_extend.sort_values(by=['subject'])  # sort values

    # RECREATE Column names smaller
    re_create = True
    if re_create:
        profile_df = recreate_column_names(profile_df)
        profile_df_nr = recreate_column_names(profile_df_nr)
        profile_df_extend = recreate_column_names(profile_df_extend)

    # SAVE
    filename = studyname
    # to_excel
    writer = pd.ExcelWriter(os.path.join(outdir, filename) + '.xlsx')
    profile_df.to_excel(writer, 'Sheet1')
    profile_df_nr.to_excel(writer, 'Sheet2')
    profile_df_extend.to_excel(writer, 'Sheet3')
    writer.save()
    # to_pickle
    profile_df.to_pickle(os.path.join(outdir, filename) + ".pcl")


if __name__ == "__main__":
    #---DATA DIR
    # '/Volumes/Seagate/e2_priming/e2_data_da_pz_avgref' #my.get_test_folder(foldername="e2_data")#
    datadir = '/Users/nm.costa/Google_Drive/projects/phd/research/2_THESIS_PUBLICATIONS/thesis/C3_e2_results/results/eeg/e2_study_2_150uV_pz_avgref'
    # outdir
    outdir = datadir  # my.get_test_folder(foldername="e2_profile_study")#

    # band
    band = "beta"

    # study name
    studyname = band + "_" + "test_1_ratio_power_threshold"

    play_subject_profile(datadir, outdir, band=band, studyname=studyname)
