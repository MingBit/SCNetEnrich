#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 16 20:50:39 2019

@author: mwu
"""

import networkx as nx
import pandas as pd
import community
import snf
import numpy as np
import warnings

import networkx.algorithms.traversal as nextra
from NetEnrich import de_bruijn as debruijn
from NetEnrich import random_walk as rw
from BuildNet import gne_dockercaller as dc
import copy

def __init__():
       warnings.simplefilter("ignore")

def get_centrality(gnetdata):

        """ returns betweeness, closeness, degree and pageRank
        """
        G = gnetdata.NetAttrs['graph']
        centralities = pd.DataFrame(list(G.node), columns=['node'])
        centralities['betweenness'] = pd.DataFrame.from_dict(list(nx.betweenness_centrality(G).items()))[1]
        centralities['closeness'] = pd.DataFrame.from_dict(list(nx.closeness_centrality(G).items()))[1]
        centralities['degree'] = pd.DataFrame.from_dict(list(nx.degree_centrality(G).items()))[1]
        centralities['pageRank'] = pd.DataFrame.from_dict(list(nx.degree_centrality(G).items()))[1]

        gnetdata.NetAttrs['centralities'] = centralities
        return(gnetdata)

def community_detect(gnetdata):

        """return predicted communities
        """
        #TODO: more robust
        G = gnetdata.NetAttrs['graph']
        subpara = {}
#        colors = sns.color_palette() + sns.color_palette('Paired', 100)
        partition = community.best_partition(G, **subpara)
        communities = pd.DataFrame.from_dict(list(partition.items()))
        communities.columns = ['node', 'group']

        gnetdata.NetAttrs['communities'] = communities


        return(gnetdata)

def _linkage_to_adjlink(linkage_table, node_list):
        """convert linkage table to weighted adjacency matrix
        """

        adjlink_matrix = pd.DataFrame(0, columns=node_list, index = node_list, dtype = np.float)
#        source, target, score = list(linkage_table.columns)
        for i in range(0, len(linkage_table)):
                if (linkage_table['source'][i] in node_list) & (linkage_table['target'][i] in node_list):
                        adjlink_matrix.loc[linkage_table['source'][i]][linkage_table['target'][i]] = linkage_table['weight'][i]
                        adjlink_matrix.loc[linkage_table['target'][i]][linkage_table['source'][i]] = linkage_table['weight'][i]
                else: break
        return np.array(adjlink_matrix)



def _knn_based_merge(link_1, link_2):

        node_list = list(set(link_1['source']) & set(link_1['target']) & set(link_2['source']) & set(link_2['target']))

        adjlink_1 = _linkage_to_adjlink(link_1, node_list)
        adjlink_2 = _linkage_to_adjlink(link_2, node_list)
        adjlinks = list()
        adjlinks.append(adjlink_1)
        adjlinks.append(adjlink_2)
        affinity_matrix = snf.make_affinity(adjlinks)
        fused_network = snf.snf(affinity_matrix)
        Graph = nx.from_numpy_matrix(fused_network)

        return(Graph)



def graph_merge(link_1, link_2, method = 'union'):

        """it returns the merged network
        """
        if method == 'union':
                union_links = pd.merge(link_1, link_2, how = 'outer')
                dc._remove_duplicate(union_links)
                mergedlinks = union_links.groupby(['source', 'target'], as_index = False).mean().reindex()
                Graph = nx.from_pandas_edgelist(mergedlinks,
                                    source = 'source',
                                    target= 'target',
                                    edge_attr = True)

        elif method == 'intersection':

                link_1_cp = copy.deepcopy(link_1)
                link_1_cp.columns = ['target', 'source', 'weight']
                inter_links_1 = pd.merge(link_1, link_2, how = 'inner')
                inter_links_2= pd.merge(link_1_cp, link_2, how = 'inner')
                inter_links = pd.merge(inter_links_1, inter_links_2, how = 'outer')
                mergedlinks = inter_links.groupby(['source', 'target'], as_index = False).mean().reindex()
                Graph = nx.from_pandas_edgelist(mergedlinks,
                                    source = 'source',
                                    target= 'target',
                                    edge_attr = True)
        elif method == 'knn':

                Graph = _knn_based_merge(link_1, link_2)

        else:

                raise Exception('valid method parameter: union, intersection, knn!')

        return(Graph)


def graph_traveral(graph, start, threshold, method = 'bfs'):
        """for given network and start point, it generates a path in a specific manner
        """

        if method == 'bfs':

                res_path = nextra.bfs_tree(G = graph, source=start, depth_limit=threshold)

        elif method == 'dfs':

                res_path = nextra.dfs_tree(G = graph, source = start, depth_limit = threshold)
        else:
                raise Exception('valid method parameter: bfs, dfs!')

        return(res_path)


def random_walk(gnetdata, start, supervisedby, steps):

        """perform supervided random walk for given steps and weights
        """

        path = rw.supervised_random_walk(gnetdata = gnetdata, start = start, supervisedby = supervisedby, steps = steps)
        return(path)


def path_merge(path_1, path_2, k_mer = 3, path = 'Eulerian'):
        """ perform de bruijn graph mapping for ginve two path lists
        """
        g = debruijn.construct_graph([path_1, path_2], k_mer)
        merged_path = debruijn.output_contigs(g)

        return merged_path





# =============================================================================
# TODO: def graph_enrichment(gnetdata_1, gnetdata_2, filteredby = 'pageRank'):
#
# =============================================================================







