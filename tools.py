# coding:utf-8
import json
import re
import random
from collections import Counter


def get_json_data(json_file):
    with open(json_file, 'r', encoding='utf-8')as file:
        data=json.loads(file.read())
    return data

def cut_json_data(data_file,des_file,start_idx,end_idx):
    data=get_json_data(data_file)
    save_json(data[start_idx:end_idx],des_file)

def list_count_sort(l):
    """按list出现次数排序"""
    s = Counter(l)
    sorted_s = sorted(s.items(), key=lambda x: x[1], reverse=True)
    return [i[0] for i in sorted_s]

def list2dict(l,reverse=True):
    """
    将列表出现的相同字符进行计数，顺便进行排序
    """
    res=dict()
    for i in l:res[i]=res.setdefault(i,0)+1
    res=sort_dict(res,reverse=reverse)
    return res

def cut_data(data,rate="default"):
    """
    切分列表（数据集常用）
    :param data:列表
    :param rate:切分比率，默认8:1:1 (不是严格的比率，会有整数问题)
    :param dev:是否需要dev
    :return:
    """
    if rate=="default":rate=[0.8,0.1,0.1]
    elif sum(rate)!=1: raise Exception("概率和不等于1")
    amount=[int(len(data)*i) for i in rate]
    for i in range(1,len(amount)):
        amount[i]+=amount[i-1]
    amount[-1]=len(data)
    amount=[0]+amount
    cutted_data=tuple()
    for i in range(len(amount)-1):
        cutted_data+=(data[amount[i]:amount[i+1]],)

    return cutted_data

def sort_dict(source_dict,obj="value",reverse=True):
    """
    对字典排序，可按值或按键
    :param source_dict:
    :param obj:
    :return:
    """
    if obj=="value":
        return {k: v for k, v in sorted(source_dict.items(), key=lambda item: item[1], reverse=reverse)}
    else:
        return {k: v for k, v in sorted(source_dict.items(), key=lambda item: item[0], reverse=reverse)}

def get_first_pattern(patterns,s):
    """返回模式列表中第一个匹配的模式，没有返回None"""
    if s:
        for pattern in patterns:
            ret = re.search(pattern, s)
            if ret:
                return ret.group()

def save_json(data,filename):
    """将数据保存在json文件中"""

    data = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(data)

def filter_chinese(s):
    """只剩中文字符,但不包含数字"""
    res=re.findall("[\u4e00-\u9fa51234567890]",s)
    if res:return "".join(res)

def get_values(obj_attribute,json_file):
    """
    返回特定属性的属性值列表
    :param obj_attribute: 特定属性名称
    :param json_file: 目标文件
    :return: 属性值列表
    """
    with open(json_file,'r',encoding='utf-8')as file:
        data=json.loads(file.read())
    values=[]
    for item in data:
        for attribute,value in item["infobox"].items():
            if re.search(attribute,obj_attribute):
                values.append(value)
    return values

def create_value_vocab(values,obj_file,limit_count=2,limit_len=2):
    """
    将所有属性值变成词典
    :param values: 要抽的属性值列表
    :param obj_file: 结果存储
    :param limit_count: 最小出现次数
    :param limit_len: 最小长度
    :return:词典列表
    """
    value_vocab=dict()
    for value in values:
        if value!=filter_chinese(value):continue  #包含除中文以外的字符删除掉
        if len(value)<limit_len:continue  #长度为1删除
        if "的" in value:continue  #出现非国家字符删除
        if value in value_vocab.keys():value_vocab[value]+=1
        else:value_vocab[value]=1
    value_vocab = {k:v for k,v in value_vocab.items() if v>=limit_count} #将只出现一次的删除
    value_vocab= [k for k,v in sorted(value_vocab.items(), key=lambda d: d[1], reverse=True)]

    #将重复的子串去掉
    value_vocab_set=set()
    for value in value_vocab:
        flag=True
        for i in range(2,len(value)):
            if value[:i] in value_vocab_set or value[-i:] in value_vocab_set:
                flag=False
                break
        if flag:value_vocab_set.add(value)
    value_vocab=list(value_vocab_set)

    value_vocab = sorted(value_vocab, key=lambda i: len(i), reverse=False)
    save_json(value_vocab,obj_file)
    return value_vocab

def strB2Q(ustring):
    """让阿拉伯数字为半角，其余为全角"""
    """数字会变化"""
    rstring = ""
    for uchar in ustring:
        inside_code=ord(uchar)
        if inside_code == 32:                                 #半角空格直接转化
            inside_code = 12288
        elif inside_code >= 32 and inside_code <= 126:        #半角字符（除空格）根据关系转化
            inside_code += 65248

        rstring += chr(inside_code)

    num_Qstr="１２３４５６７８９０"
    num_Bstr="1234567890"
    for i in range(10):
        rstring=rstring.replace(num_Qstr[i],num_Bstr[i])
    return rstring

def strQ2B(ustring):
    """把字符串全角转半角"""
    def Q2B(uchar):
        """单个字符 全角转半角"""
        inside_code = ord(uchar)
        if inside_code == 0x3000:
            inside_code = 0x0020
        else:
            inside_code -= 0xfee0
        if inside_code < 0x0020 or inside_code > 0x7e: #转完之后不是半角字符返回原来的字符
            return uchar
        return chr(inside_code)
    return "".join([Q2B(uchar) for uchar in ustring])

def filter_line(s):

    """
    对一行中文文本过滤，将无效的信息删除
    """
    if s :
        useless_note=" \n"
        for i in useless_note:s=s.replace(i,"")
        if s:return s

def entity2BIO(attribute, value, sep, mode):
    """
    将实体转换为BIO字符串
    """
    if mode == "BIO":
        res = [value[0] + sep + "B-" + attribute]
        for i in range(1, len(value)):
            res.append(value[i] + sep + "I-" + attribute)
    else:
        if len(value) == 1:
            return value + sep + "S-" + attribute
        res = [value[0] + sep + "B-" + attribute]
        for i in range(1, len(value) - 1):
            res.append(value[i] + sep + "I-" + attribute)
        res.append(value[-1] + sep + "E-" + attribute)
    return res

def json2BIO(json_file,BIO_file,sep="\t",mode="BIOES"):
    "将json里面的文件转化为BIO文件"
    def process_summary(summary):
        end_note=set(",，。.")
        new_summary=[]
        for i in range(len(summary)):
            if summary[i] not in end_note:
                if summary[i][0] in end_note:summary[i]=summary[i][1:]
                if summary[i][-1] in end_note:summary[i] = summary[i][:-1]
                new_summary.append(summary[i])
        return "，".join(new_summary)

    data=get_json_data(json_file)


    with open(BIO_file,'w',encoding='utf-8')as file:
        for item in data:
            BIO_sentence=[]
            infobox=item['infobox']
            summary=item['summary']
            summary=process_summary(summary)
            index=0
            while(index<len(summary)):
                flag=True
                for attribute, value in infobox.items():
                    if summary[index:index+len(value)]==value:
                        BIO_sentence+=entity2BIO(attribute,value,sep,mode)
                        index+=len(value)
                        flag=False
                        break
                if flag:
                    BIO_sentence.append(summary[index]+sep+"O")
                    index+=1
            BIO_sentence="\n".join(BIO_sentence)+"\n\n"
            file.write(BIO_sentence)

def limit_attribute_nums(json_file,new_json_file,limit_num):
    data = get_json_data(json_file)
    new_data = []
    for item in data:
        if len(item["infobox"]) >= limit_num: new_data.append(item)
    save_json(new_data, new_json_file)

def get_remote_json_info(json_file):
    data = get_json_data(json_file)
    res = dict()
    res["条目数"] = len(data)
    res["属性分布"] = dict()
    sentence_len = []  # 句子长度
    attribute_len=[]
    for item in data:
        if "para" in item.keys():
            item["summary"]=item["para"]+[item["summary"]]
        attribute_len.append(len(item["infobox"]))
        for attribute in item["infobox"].keys():
            if attribute in res["属性分布"].keys():
                res["属性分布"][attribute] += 1
            else:
                res["属性分布"][attribute] = 1
            sentence_len.append( sum([len(i) for i in item["summary"]]))
    res["属性分布"] = sort_dict(res["属性分布"])
    res["平均句长"] = sum(sentence_len) / res["条目数"]
    # res["句长分布"]=sort_dict(list2dict(sentence_len),obj="value",reverse=False)
    res["属性数量分布"] = sort_dict(list2dict(attribute_len), obj="value", reverse=False)
    res["平均属性数量"]=sum(attribute_len)/len(attribute_len)
    for key, value in res.items():
        print(key + ":")
        print(value)
    return res
    
def get_value_distribution(json_file,attribute_name):

    data=get_json_data(json_file)
    value_dict=dict()
    for item in data:
        if attribute_name in item["infobox"].keys():
            value=item["infobox"][attribute_name]
            value_dict[value]=value_dict.setdefault(value,0)+1
    return sort_dict(value_dict)

def get_attribute_distribution(json_file):
    def percentage(num):
        """将小数转化成百分比格式,保留两位小数"""
        return str(int(num*10000)/100)+"%"

    data=get_json_data(json_file)
    person_num=len(data)
    attributes=[]
    for item in data:
        attributes+=item["infobox"]
    attributes=list2dict(attributes)
    for i in attributes.keys():
        attributes[i]=percentage(attributes[i]/person_num)

    return attributes

def data2excel(data, des_file, mode="dict1",columns=[]):
    """
    将数据有格式的保存在excel中
    默认格式为二维列表（最终都要转化成二维列表）
    """
    import pandas as pd
    if mode=="dict1":
        """一维字典，单纯的属性+值"""
        if not columns:columns=["key","value"]
        data=[list(item)for item in data.items()]

    elif mode=="dict2":
        """
        二维字典
        要求字典的键格式必须一样
        """
        new_data = []
        columns = list(data[list(data.keys())[0]].keys())
        for key, value in data.items():
            item = [key]
            for key2 in columns:
                item.append(value[key2])
            new_data.append(item)
            data = new_data
        columns=["name"]+columns
    elif mode=="list2":
        """二维列表"""
        if not columns: columns = ["PAD"]*len(data[0])
    df = pd.DataFrame(data, columns=columns)
    df.to_excel(des_file, index=False)

def json2mrc(json_file,des_mrc_dir,mode="BIOES",sep="\t"):

    def get_question(attribute):
        return "该人物的"+attribute+"是什么?"

    def BIO_mark(line,attribute,values):
        BIO_sentence=[]
        if not isinstance(values,list):values=[values]
        index = 0
        while (index < len(line)):
            flag=True
            for value in values:
                if line[index:index + len(value)] == value:
                    BIO_sentence += entity2BIO(value=value, sep=sep,attribute=attribute,mode=mode)
                    index += len(value)
                    flag=False
                    break
            if flag:
                BIO_sentence.append(line[index] + sep + "O")
                index += 1
        return "\n".join(BIO_sentence)

    data = get_json_data(json_file)

    new_data=[]
    for item in data:
        infobox = item['infobox']
        summary = item['summary']
        for attribute, value in infobox.items():
            if isinstance(value, list):
                flag=False
                for line in item['summary']:
                    line=line[:1000]
                    for v in value:
                        if v in line:
                            new_data.append(get_question(attribute)+"\n"+BIO_mark(line,attribute,value))
                            flag=True
                            break
                    if flag:break
            else:
                for line in summary:
                    if value in line:
                        new_data.append(get_question(attribute)+"\n"+BIO_mark(line,attribute,value))
                        break
    random.shuffle(new_data)
    print(len(new_data))
    train_data,test_data,dev_data=cut_data(new_data)
    train_data="\n\n".join(train_data)
    test_data="\n\n".join(test_data)
    dev_data = "\n\n".join(dev_data)
    with open(des_mrc_dir+"/train.txt", 'w', encoding='utf-8')as file:
        file.write(train_data)
    with open(des_mrc_dir+"/test.txt", 'w', encoding='utf-8')as file:
        file.write(test_data)
    with open(des_mrc_dir+"/dev.txt", 'w', encoding='utf-8')as file:
        file.write(dev_data)

def get_data_index(data_file,des_file,start,end):

    data=get_json_data(data_file)
    save_json(data[start:end],des_file)

def json2mrc_all(json_file,des_mrc_dir,sep="\t"):
    """
    造全部的数据，包括负样例
    :param attributes: 应该标的属性值
    :param json_file: 原数据
    :param des_mrc_dir: 目录，包含两个文件
        dev.txt，造好的数据
        dev_info.json：infobox和句子长度
    :param sep:
    :return:
    """
    def get_question(attribute):
        return "该人物的"+attribute+"是什么?"

    def BIO_mark(sentence):
        BIO_sentence=[i + sep + "O" for i in sentence]
        return "\n".join(BIO_sentence)

    data = get_json_data(json_file)

    new_data=[]
    new_info=[]
    attributes = [
        # 先前的属性
        "国籍", "性别", "身高", "体重", "民族", "学历", "毕业院校", "出生地", "出生日期", "逝世日期",
        # 后加的属性
        "姓名", "外文名", "运动项目", "所属运动队", "场上位置", "信仰"
    ]
    for item in data:
        if "para" in item.keys():sentences = [item['summary']]+item["para"]
        else:sentences = item['summary']
        sentences_count=0
        for sentence in sentences:
            for attribute in attributes:
                new_data.append(get_question(attribute) + "\n" + BIO_mark(sentence))
                sentences_count+=1
        new_info.append({"infobox":item['infobox'],"sentence_len":sentences_count})

    print(len(new_data))
    new_data="\n\n".join(new_data)
    dev=des_mrc_dir+"/dev.txt"
    dev_info=des_mrc_dir+"/dev_info.json"
    with open(dev, 'w', encoding='utf-8')as file:
        file.write(new_data)
    save_json(new_info,dev_info)

get_remote_json_info("output/remote_supervision_result_process.json")