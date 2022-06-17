import copy
import json
import itertools
import os
import re
import numpy as np
import pandas as pd
import backend.utils.fileUtil as fileUtil
from backend.utils.dataStructure import ProjectFilesTrieTree, SectionFilesTrieTree, UnionFind
from django.conf import settings
from asgiref.sync import async_to_sync
from backend import models
from backend import serializers
from channels.layers import get_channel_layer

CLUSTER_TYPES_LIST = ['Central', 'Core', 'Control', 'Shared', 'Peripheral']


def get_projectFiles_data(contents, parent_pk_dict):
    projectFiles_data = []
    for sub_folder in settings.PROJECTFILE_SUB_FOLDER:
        for selector in contents[sub_folder]:
            file_name = selector['file_name']
            item = {
                'file': selector['file'],
                'file_name': os.path.splitext(file_name)[0],
                'file_extension': os.path.splitext(file_name)[1].strip('.'),
                'file_type': settings.PROJECTFILE_SUB_FOLDER_DICT[sub_folder],
                'status': False,
                'parent_file': parent_pk_dict[sub_folder],
            }
            projectFiles_data.append(item)
    return projectFiles_data


def post_projectFiles_data(ori_file, file_name, parent_file_dict, channel_id):
    file = models.ProjectFiles.objects.get(id=ori_file).file.file
    contents = fileUtil.un_zip_projectFile(file, file_name)
    projectFiles_data = get_projectFiles_data(contents, parent_file_dict)
    serializer = serializers.ProjectFilesSerializer(data=projectFiles_data,
                                                    many=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    df_structure = pd.DataFrame(contents.get('structure'))
    df_relation = pd.DataFrame(contents.get('relation'))
    df_relation['file_name'] = df_relation['file_name'].apply(
        lambda x: x.replace('-out', ''))
    df_structure = pd.merge(df_structure, df_relation, on=['file_name'])
    structure_file_list = list(
        filter(
            lambda x: x['parent_file'] == parent_file_dict.get(
                'structure'), serializer.data))
    for structure_file in structure_file_list:
        serializer = serializers.CatelogueDatasSerializer(
            data={
                'name':
                    structure_file.get('file_name').replace(
                        '{}_'.format(file_name), ''),
                'structure_file':
                    structure_file.get('id')
            })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        parent_pk = serializer.data['id']

        temp_name = '{}.json'.format(structure_file.get('file_name'))
        index = df_structure[df_structure['file_name'] ==
                             temp_name].index.tolist()[0]
        structure_content = df_structure.at[index, 'file_x']
        relation_content = df_structure.at[index, 'file_y']
        serializer = serializers.CatelogueTreeMapDatasSerializer(
            data={
                'name': 'root',
                'structure_file': structure_file['id'],
                'value': [],
                'relation': json.dumps({})
            })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        root_pk = serializer.data['id']
        count_content = models.ProjectFiles.objects.filter(
            parent_file=parent_file_dict.get('count')).first()
        serializer = serializers.ClusterDatasSerializer(
            data={'name': 'root', 'cluster': 0, 'relation': json.dumps({}), 'structure_file': structure_file['id']})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        cluster_root_pk = serializer.data['id']
        result, edges_result, cluster_data, tree_data = post_catelogueDatas_data(
            structure_content, count_content, relation_content, parent_pk,
            root_pk, structure_file.get('id'), cluster_root_pk)
        serializer = serializers.SubCatelogueDatasSerializer(data=result,
                                                             many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = serializers.ProjectFileEdgesSerializer(data=edges_result, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        for selector in cluster_data:
            serializer = serializers.ClusterDatasSerializer(data=selector[0])
            serializer.is_valid(raise_exception=True)
            serializer.save()
            serializer = serializers.ClusterDatasSerializer(data=selector[1:], many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        for selector in tree_data:
            serializer = serializers.CatelogueTreeMapDatasSerializer(
                data=selector, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
    # channels_layer = get_channel_layer()
    # send_dict = {
    #     "type": "send.message",
    #     "message": {
    #         'percent': 50,
    #         'uploadStatus': 'normal',
    #     }
    # }
    # structure_file_status = []
    # number = 0
    # try:
    #     file = models.ProjectFiles.objects.get(id=ori_file).file.file
    #     contents = fileUtil.un_zip_projectFile(file, file_name)
    #     projectFiles_data = get_projectFiles_data(contents, parent_file_dict)
    #     serializer = serializers.ProjectFilesSerializer(data=projectFiles_data,
    #                                                     many=True)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     df_structure = pd.DataFrame(contents.get('structure'))
    #     df_relation = pd.DataFrame(contents.get('relation'))
    #     df_relation['file_name'] = df_relation['file_name'].apply(
    #         lambda x: x.replace('-out', ''))
    #     df_structure = pd.merge(df_structure, df_relation, on=['file_name'])
    #     structure_file_list = list(
    #         filter(
    #             lambda x: x['parent_file'] == parent_file_dict.get(
    #                 'structure'), serializer.data))
    #     for structure_file in structure_file_list:
    #         serializer = serializers.CatelogueDatasSerializer(
    #             data={
    #                 'name':
    #                     structure_file.get('file_name').replace(
    #                         '{}_'.format(file_name), ''),
    #                 'structure_file':
    #                     structure_file.get('id')
    #             })
    #         serializer.is_valid(raise_exception=True)
    #         serializer.save()
    #         parent_pk = serializer.data['id']
    #
    #         temp_name = '{}.json'.format(structure_file.get('file_name'))
    #         index = df_structure[df_structure['file_name'] ==
    #                              temp_name].index.tolist()[0]
    #         structure_content = df_structure.at[index, 'file_x']
    #         relation_content = df_structure.at[index, 'file_y']
    #         serializer = serializers.CatelogueTreeMapDatasSerializer(
    #             data={
    #                 'name': 'root',
    #                 'structure_file': structure_file['id'],
    #                 'value': [],
    #                 'relation': json.dumps({})
    #             })
    #         serializer.is_valid(raise_exception=True)
    #         serializer.save()
    #         root_pk = serializer.data['id']
    #         count_content = models.ProjectFiles.objects.filter(
    #             parent_file=parent_file_dict.get('count')).first()
    #         serializer = serializers.ClusterDatasSerializer(
    #              data={'name': 'root', 'cluster': 0, 'relation': json.dumps({}), 'structure_file': structure_file['id']})
    #         serializer.is_valid(raise_exception=True)
    #         serializer.save()
    #         cluster_root_pk = serializer.data['id']
    #         result, cluster_data, tree_data = post_catelogueDatas_data(
    #             structure_content, count_content, relation_content, parent_pk,
    #             root_pk, structure_file.get('id'), cluster_root_pk)
    #         serializer = serializers.SubCatelogueDatasSerializer(data=result,
    #                                                              many=True)
    #         serializer.is_valid(raise_exception=True)
    #         serializer.save()
    #         for selector in cluster_data:
    #             serializer = serializers.ClusterDatasSerializer(data=selector[0])
    #             serializer.is_valid(raise_exception=True)
    #             serializer.save()
    #             serializer = serializers.ClusterDatasSerializer(data=selector[1:], many=True)
    #             serializer.is_valid(raise_exception=True)
    #             serializer.save()
    #         for selector in tree_data:
    #             serializer = serializers.CatelogueTreeMapDatasSerializer(
    #                 data=selector, many=True)
    #             serializer.is_valid(raise_exception=True)
    #             serializer.save()
    #         structure_file_status.append(structure_file.get('id'))
    #         number += 1
    #         send_dict = {
    #             "type": "send.message",
    #             "message": {
    #                 'percent': 50 + number / len(structure_file_list) * 50,
    #                 'uploadStatus': 'uploading',
    #             }
    #         }
    #         async_to_sync(channels_layer.group_send)(channel_id, send_dict)
    #     send_dict['message']['uploadStatus'] = 'success'
    #     async_to_sync(channels_layer.group_send)(channel_id, send_dict)
    # except Exception:
    #     send_dict['message']['uploadStatus'] = 'error'
    #     async_to_sync(channels_layer.group_send)(channel_id, send_dict)
    # finally:
    #     send_dict['message']['uploadStatus'] = 'closed'
    #     async_to_sync(channels_layer.group_send)(channel_id, send_dict)
    #     models.ProjectFiles.objects.filter(
    #         id__in=structure_file_status).update(status=True)


def post_catelogueDatas_data(project_file, count_file, relation_file,
                             parent_id, root_id, structure_file, cluster_root_pk):
    json_object = json.loads(project_file.file.getvalue())
    df_count = pd.read_csv(count_file.file.url)

    # 读取统计文件
    df_count.rename(columns={
        'filename': 'name',
        'changeloc': 'changeLoc'
    },
        inplace=True)
    df_project = pd.DataFrame({'name': json_object['variables']})
    df_project['name'] = df_project['name'].apply(
        lambda x: re.sub(r'(.+)base/', '', x.replace('\\', '/')))
    df_merge = pd.merge(df_project,
                        df_count.loc[:, ['name', 'changeLoc']],
                        on='name')
    df_merge['name'] = df_merge['name'].apply(
        lambda x: count_standardization(x))
    df_merge['color'] = df_merge['changeLoc'].apply(
        lambda x: get_color_by_changeLoc(x))
    df_merge['catelogue_type'] = 2
    df_merge['parent_catelogue'] = parent_id
    df_merge['structure_file'] = structure_file
    df_merge['value'] = df_merge['changeLoc'].apply(
        lambda x: get_value_by_changeLoc(x))
    df_merge['_id'] = df_merge.index.to_list()
    df_merge['_id'] = df_merge['_id'].astype(int)

    df_cells = pd.DataFrame([{
        'id': selector[0],
        'source': selector[1]['src'],
        'target': selector[1]['dest'],
        'values': json.dumps(selector[1]['values'])
    } for selector in enumerate(json_object['cells'])])
    df_cells['structure_file'] = structure_file

    # 读取依赖文件
    df_relation = get_relation_result_df(relation_file)
    df_drop = df_merge.append(df_relation).drop_duplicates(['name'],
                                                           keep=False)
    df_drop.drop(df_drop[np.isnan(df_drop['changeLoc'])].index, inplace=True)
    df_result = pd.merge(df_merge, df_relation, on='name').append(df_drop)
    df_result.sort_index(ignore_index=True, inplace=True)
    df_result.fillna(json.dumps(dict()), inplace=True)
    df_result['catelogue_type'] = df_result['catelogue_type'].astype(int)
    cells_groupby_dict = dict([(selector[0],
                                dict((item.get('target'), json.loads(item.get('values'))) for item in
                                     selector[1].loc[:, ['target', 'values']].to_dict(orient='records')))
                               for selector in list(df_cells.groupby(by=['source']))])
    df_result['cells'] = df_result['_id'].apply(lambda x: json.dumps(cells_groupby_dict.get(x)))
    df_result['cells'].fillna(json.dumps({}), inplace=True)
    cluster_data_list = post_cluster_data(df_result, df_cells, structure_file, cluster_root_pk)
    tree_data_list = post_catelogueTreeMapDatas_data(df_result, root_id,
                                                     structure_file)
    return df_result.to_dict(orient='records'), df_cells.to_dict(orient='records'), cluster_data_list, tree_data_list


def post_catelogueTreeMapDatas_data(origin_df, root_id, structure_file):
    tree = ProjectFilesTrieTree(origin_df.max()['changeLoc'], root_id,
                                structure_file)
    origin_df.apply(
        lambda x: tree.insert(x['name'].split('/'), x['changeLoc']), axis=1)
    df = pd.DataFrame(tree.getRoot())
    df.drop(index=df.loc[(df['name'] == 'root')].index, inplace=True)
    origin_df['qualifiedName'] = origin_df['name']
    origin_df = origin_df.loc[:, ['qualifiedName', 'color', 'relation']]
    df_drop = df[df['end'] == False]
    df_merge = pd.merge(df, origin_df, on='qualifiedName')
    df_result = df_drop.append(df_merge)
    df_result['color'].fillna('#C0C0C0', inplace=True)
    df_result['id'] = df_result['id'].astype(int)
    df_result['relation'].fillna(json.dumps(dict()), inplace=True)
    df_result['structure_file'] = structure_file
    df_result.sort_values(by=['catelogue_type', 'id'], inplace=True)
    groupby_list = [
        selector[1].to_dict(orient='records')
        for selector in list(df_result.groupby(['catelogue_type']))
    ]
    return groupby_list


def post_cluster_data(df_nodes, df_edges, structure_file, cluster_root_pk):
    count = cluster_root_pk
    matrix = get_adjacency_matrix(df_nodes, df_edges)
    matrix = warshall(matrix)  # 可达性矩阵
    items = figure_matrix(matrix)  # 度量
    df = pd.DataFrame(items)
    df.sort_values(by=['VFI', 'VFO'], ascending=(False, True),
                   inplace=True)  # VFI降序,VFO升序排列
    group_list = judge_group(df, matrix)
    datas = {'VFI': [], 'VFO': [], 'length': []}
    for group in group_list:
        datas.get('VFI').append(int(df.at[group[0], 'VFI']))
        datas.get('VFO').append(int(df.at[group[0], 'VFO']))
        datas.get('length').append(len(group))
    architecture_type = architecture_classify(datas)
    type_list = element_classify(architecture_type, datas, group_list)
    df_nodes['cluster_type'] = type_list
    df_nodes['groupNumber'] = get_group_number(df_nodes.index.to_list(), group_list)
    nodes_groupby_list = list(df_nodes.groupby(by=['cluster_type']))
    temp_list, result_list = dict([(item, []) for item in CLUSTER_TYPES_LIST]), []
    for item in nodes_groupby_list:
        cluster_type = item[0]
        # 按groupNumber聚类
        group_number_list = list(item[1].groupby(by=['groupNumber']))
        # 对groupNumber重新索引至每个类别下
        group_number_list = dict(
            map(lambda x: (x[1][0], x[0] + 1), enumerate(group_number_list)))
        item[1]['groupNumber'] = item[1]['groupNumber'].apply(
            lambda x: group_number_list.get(x))
        item[1].apply(lambda x: temp_list.get(cluster_type).append(x.to_dict()), axis=1)

    def appendFunc(df_temp, count):
        df_temp.reset_index(inplace=True)
        number = count + 1
        temp = []
        temp.append(
            {'id': number, 'cluster': 1, 'name': item[0], 'parent_node': cluster_root_pk, 'relation': json.dumps({}),
             'structure_file': structure_file})
        df_temp['id'] = df_temp.index.to_list()
        df_temp['id'] = df_temp['id'].apply(lambda x: x + number + 1)
        df_temp['cluster'] = 2
        df_temp['parent_node'] = number
        number = df_temp['id'].tail(1).to_list()[0]
        temp.extend(df_temp.to_dict(orient='record'))
        result_list.append(temp)
        return number

    for item in temp_list.items():
        if item[0] != 'Peripheral' and len(item[1]):
            count = appendFunc(pd.DataFrame(item[1]), count)
        elif item[0] == 'Peripheral' and len(item[1]):
            peripheral_groupby_list = list(
                pd.DataFrame(item[1]).groupby(by=['groupNumber']))
            for selector in peripheral_groupby_list:
                df_temp = selector[1]
                count = appendFunc(df_temp, count)
    return result_list


def get_value_by_changeLoc(number, time=100):
    if 0 <= number <= 100:
        return 0.25 * time
    elif 100 < number <= 500:
        return 0.3 * time
    elif 500 < number <= 1000:
        return 0.4 * time
    elif 1000 < number <= 2000:
        return 0.6 * time
    else:
        return 0.8 * time


def get_relation_result_df(relation_file):
    relation_json_object = json.loads(relation_file.file.getvalue())
    relation_df_list = [
        get_relation_df(selector[1], item[0], selector[0])
        for item in list(relation_json_object.items())
        for selector in list(item[1].items())
    ]
    relation_df = pd.concat(relation_df_list)
    relation_df.sort_index(ignore_index=True, inplace=True)
    relation_df['name'] = relation_df['src'].apply(
        lambda x: relation_standardization(x))
    relation_filter_df = relation_df.loc[relation_df['name'].str.contains('/'),
                                         ['name', 'meta', 'operator']]
    groupby_name_list = list(relation_filter_df.groupby(['name']))
    groupby_meta_list = [{
        'name': item[0],
        'relation': list(item[1].groupby(['meta']))
    } for item in groupby_name_list]
    groupby_result_list = \
        [{'name': selector.get('name'),
          'relation': json.dumps(dict([(
              item[0], item[1].loc[:, ['meta', 'operator']].groupby(['operator']).count().to_dict().get('meta')) for
              item in selector.get('relation')]))} for selector in groupby_meta_list]
    return pd.DataFrame(groupby_result_list)


def count_standardization(string):
    if string.find('com') != -1:
        return string[string.find('com'):string.find('.')]
    return string[string.find('android'):string.find('.')]


def get_relation_df(json_dict, meta, operator):
    df = pd.DataFrame(json_dict)
    df['meta'] = meta
    df['operator'] = operator
    return df


def relation_standardization(string):
    string = string.replace('.', '/')
    patterns = ['([a-z]*/)*([A-Z].*?/)', '([a-z]*/)*([A-Z].*)']
    results = list(
        filter(lambda x: x is not None,
               map(lambda y: re.search(y, string), patterns)))
    result = '' if len(results) == 0 else results[0].group() if len(
        results) == 1 else results[0].group()[:-1]
    return result


def get_color_by_changeLoc(number):
    color_list = ['#247ba0', '#70c1b3', '#b2dbbf', '#f3ffbd', '#ff1654']
    if 0 <= number <= 100:
        index = 0
    elif 100 < number <= 500:
        index = 1
    elif 500 < number <= 1000:
        index = 2
    elif 1000 < number <= 2000:
        index = 3
    else:
        index = 4
    return color_list[index]


# 获得邻接矩阵
def get_adjacency_matrix(df_nodes, df_edges):
    size = df_nodes.shape[0]
    matrix = np.zeros((size, size), dtype=int)
    for index, row in df_edges.iterrows():
        source = row['source']
        target = row['target']
        if source < size and target < size:
            matrix[source][target] = 1
    return matrix


# warshall算法求可达性矩阵
def warshall(matrix):
    length = len(matrix)
    for i in range(length):
        for j in range(length):
            if matrix[j][i] == 1:
                for k in range(length):
                    matrix[j, k] += matrix[i, k]
    for i in range(length):
        for j in range(length):
            if i == j and matrix[i][j] == 0:
                matrix[i][j] = 1
    matrix = np.int64(matrix > 0)
    return matrix


# 计算矩阵中每个元素的VFI和VFO
def figure_matrix(matrix):
    items = [{
        'VFI': np.sum(matrix[:, i]),
        'VFO': np.sum(matrix[i, :])
    } for i in range(len(matrix))]
    return items


# 寻找循环群
def judge_group(df, matrix):
    # 获取重复值index
    not_duplicated_indexes = df.drop_duplicates(keep=False).index.to_list()
    df_duplicated = df[df.duplicated(keep=False)]
    groupby_list = df_duplicated.groupby(
        list(df_duplicated)).apply(lambda x: tuple(x.index)).tolist()
    group_list = copy.deepcopy(groupby_list)
    # 算法(2),(3)
    judge_list0 = [np.all(matrix[i, :][:, i] == 1) for i in groupby_list]
    # 算法(4)
    for selector in list(
            itertools.filterfalse(lambda x: x[1] != False,
                                  zip(group_list, judge_list0))):
        group_list.remove(selector[0])
        # 求两步的结果
        two_combine = list(itertools.combinations(selector[0], 2))
        temp = [get_sub_matrix(matrix, item) for item in two_combine]
        if len(list(itertools.filterfalse(lambda x: x[1] != False,
                                          temp))) == len(two_combine):
            group_list.extend([(item,) for item in selector[0]])
        else:
            temps = [
                item[0] for item in list(
                    itertools.filterfalse(lambda x: x[1] == False, temp))
            ]
            items = dict(
                (selector[0][i], i + 1) for i in range(len(selector[0])))
            items_reverse = dict(
                (i + 1, selector[0][i]) for i in range(len(selector[0])))
            union = UnionFind(len(selector[0]))
            for temp in temps:
                union.union(items.get(temp[0]), items.get(temp[1]))
            set_list = {}
            for i, x in enumerate(union.uf):
                if x <= -1 and i in items_reverse.keys():
                    set_list[i] = [items_reverse.get(i)]
            for i, x in enumerate(union.uf):
                if x >= 0 and i in items_reverse.keys():
                    set_list.get(x).append(items_reverse.get(i))
            set_list = list(map(tuple, set_list.values()))
            group_list.extend(set_list)
    group_list.extend([(index,) for index in not_duplicated_indexes])
    return group_list


# 获取子矩阵
def get_sub_matrix(matrix, index_list):
    return index_list, np.all(matrix[index_list, :][:, index_list] == 1)


# 判断架构类型
def architecture_classify(datas):
    temp = copy.deepcopy(datas)
    sum_group = sum(temp.get('length'))
    max_group = float(max(temp.get('length')))
    not_duplicated_list = list(set(temp.get('length')))
    not_duplicated_list.remove(max_group)
    try:
        second_max_group = float(max(not_duplicated_list))
    except ValueError:
        second_max_group = 0
    if max_group <= sum_group * 0.04:
        return 'Hierarchiacal'
    elif max_group <= second_max_group * 1.5:
        return 'Multi-core'
    elif max_group <= sum_group * 0.06:
        return 'Borderline Core-periphery'
    else:
        return 'Core-periphery'


# 判断文件类型
def element_classify(architecture_type, datas, group_list):
    element_type = ''
    type_list = [''] * sum(datas.get('length'))
    if architecture_type in ['Borderline Core-periphery', 'Core-periphery']:
        max_index = datas.get('length').index(max(datas.get('length')))
        VFI_core = datas.get('VFI')[max_index]
        VFO_core = datas.get('VFO')[max_index]
        for index, group in enumerate(group_list):
            VFI = datas.get('VFI')[index]
            VFO = datas.get('VFO')[index]
            if index != max_index:
                if VFI >= VFI_core and VFO < VFO_core:
                    element_type = 'Shared'
                elif VFI < VFI_core and VFO < VFO_core:
                    element_type = 'Peripheral'
                elif VFI < VFI_core and VFO > VFO_core:
                    element_type = 'Control'
            else:
                element_type = 'Core'
            for i in group:
                type_list[i] = element_type
    else:
        VFI_median = np.median(datas.get('VFI'))
        VFO_median = np.median(datas.get('VFO'))
        for index, group in enumerate(group_list):
            VFI = datas.get('VFI')[index]
            VFO = datas.get('VFO')[index]
            if VFI >= VFI_median and VFO < VFO_median:
                element_type = 'Shared'
            elif VFI >= VFI_median and VFO >= VFO_median:
                element_type = 'Central'
            elif VFI < VFI_median and VFO < VFO_median:
                element_type = 'Peripheral'
            elif VFI < VFO_median <= VFO:
                element_type = 'Control'
            for i in group:
                type_list[i] = element_type
    return type_list


# 获取每个节点的群号
def get_group_number(items, group_list):
    group_number_list = []
    for item in items:
        for index, group in enumerate(group_list):
            if item in group:
                group_number_list.append(index)
                break
    return group_number_list


def get_section_data(selector, df_node_list, df_edge_list):
    temp_list = [[], []]
    df_list = []
    temp = json.loads(selector['file'].file.getvalue())
    dict_list = temp['res']
    for items in dict_list:
        for item in items.items():
            if item[0] != 'values':
                temp_list[0].append(item[1])
            else:
                temp_list[1].append({
                    'source':
                        items['src']['id'],
                    'sourceFile':
                        items['src']['File'],
                    'sourcePackageName':
                        items['src']['packageName'],
                    'sourceIsHonor':
                        items['src']['not_aosp'],
                    'target':
                        items['dest']['id'],
                    'targetFile':
                        items['dest']['File'],
                    'targetPackageName':
                        items['dest']['packageName'],
                    'targetIsHonor':
                        items['dest']['not_aosp'],
                    'value':
                        list(items['values'].keys())[0]
                })
    for temp in temp_list:
        df = pd.DataFrame(temp)
        df['mode_type'] = selector['mode_type']
        df_list.append(df)
    df_node_list.append(df_list[0])
    df_edge_list.append(df_list[1])


def post_sectionFiles_data(ori_file, channel_id):
    channels_layer = get_channel_layer()
    send_dict = {
        "type": "send.message",
        "message": {
            'percent': 50,
            'uploadStatus': 'normal',
        }
    }
    try:
        async_to_sync(channels_layer.group_send)(channel_id, send_dict)

        file = models.SectionFiles.objects.get(id=ori_file).file.file
        contents = fileUtil.un_zip_sectionFile(file)
        df = pd.DataFrame(contents)
        tree = SectionFilesTrieTree(ori_file)
        df['qualifiedName'].apply(lambda x: tree.insert(x.split('/')))
        df_tree = pd.DataFrame(tree.getRoot())
        df_tree.drop(index=df_tree.loc[(df_tree['name'] == 'root')].index,
                     inplace=True)
        df_tree_drop = df_tree.loc[df_tree['end'] == False]
        df_tree_drop.rename({'name': 'file_name'}, axis=1, inplace=True)
        df_tree_drop['file_extension'] = 'folder'
        df_tree.drop(columns=['name'], inplace=True)
        df_merge = pd.merge(df, df_tree, on=['qualifiedName'])
        df_merge.sort_index(ignore_index=True, inplace=True)
        df_merge['number'] = df_merge.index
        df_merge['status'] = False
        df_node_list, df_edge_list = [], []
        for selector in enumerate(df_merge.to_dict(orient='records')):
            get_section_data(selector[1], df_node_list, df_edge_list)
            df_merge.at[selector[0], 'status'] = True
        df_nodes = pd.concat(df_node_list)
        df_temp = df_nodes.drop_duplicates(subset=['id', 'mode_type'],
                                           keep='first')
        df_temp = df_temp.groupby(['id'])['mode_type'].apply(
            lambda x: ','.join(x.values)).apply(lambda x: x.split(','))
        df_temp = pd.DataFrame([{
            '_id': item[0],
            'mode_type': item[1]
        } for item in df_temp.to_dict().items()])
        df_nodes.drop(
            ['isIntrusive', 'parameterTypes', 'rawType', 'maxTargetSdk'],
            axis=1,
            inplace=True)
        df_nodes.rename(columns={
            'id': '_id',
            'not_aosp': 'isHonor'
        },
            inplace=True)
        df_nodes['_global'] = df_nodes['global']
        df_nodes.drop(['global'], axis=1, inplace=True)
        df_nodes['modifiers'] = df_nodes['modifiers'].where(
            df_nodes['modifiers'].notnull(), 'default')
        df_nodes['modifiers'] = df_nodes['modifiers'].apply(lambda x: 'default'
        if x == '' else x)
        df_nodes = df_nodes.where(df_nodes.notnull(), None)
        df_nodes['origin_file_id'] = ori_file
        df_nodes.drop_duplicates(subset=['_id'], keep='first', inplace=True)
        df_nodes.drop('mode_type', axis=1, inplace=True)
        df_nodes = pd.merge(df_nodes, df_temp, on=['_id'], how='left')
        df_edges = pd.concat(df_edge_list)
        df_edges['origin_file_id'] = ori_file
        serializer = serializers.SectionNodesSerializer(
            data=df_nodes.to_dict(orient='records'), many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = serializers.SectionEdgesSerializer(
            data=df_edges.to_dict(orient='records'), many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        groupby_list = list(df_tree_drop.groupby(df_tree_drop['section_type']))
        for selector in enumerate(groupby_list):
            serializer = serializers.SectionFilesWriteSerializer(
                data=selector[1][1].to_dict(orient='records'), many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        serializer = serializers.SectionFilesWriteSerializer(
            data=df_merge.to_dict(orient='records'), many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        send_dict['message'] = {'percent': 100, 'uploadStatus': 'success'}
        async_to_sync(channels_layer.group_send)(channel_id, send_dict)
    except Exception:
        send_dict['message'] = {'percent': 100, 'uploadStatus': 'error'}
        async_to_sync(channels_layer.group_send)(channel_id, send_dict)
    finally:
        send_dict['message']['uploadStatus'] = 'closed'
        async_to_sync(channels_layer.group_send)(channel_id, send_dict)


def get_section_categories(data):
    df = pd.DataFrame(data[0].get('children'))
    df['name'] = df['mode_type']
    df.drop_duplicates(subset=['name'], keep='first', inplace=True)
    df.drop(index=df.loc[(df['name'] == '')].index, inplace=True)
    categories = df.loc[:, ['name']].to_dict(orient='records')
    return categories
