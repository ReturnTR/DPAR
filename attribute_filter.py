# coding:utf-8

"""
此文件包含：
属性标准化
属性过滤方法
属性归一化方法
构造数据过程
"""

from tools import *
import re
import os
from tqdm import tqdm


# 用面向对象方法解决
class AttributeInterface():
    """
    属性工具的接口，包含所有特定属性用到的功能
    """

    def __init__(self):
        self.statistics = {
            "识别出该属性数量":0,
            "无效属性值数量":0,
            "属性值在summary数量":0,
            "属性值在para数量":0,
            "多属性值数量":0,
            "文中直接抽出属性值数量":0
        }

    #必需重写的方法
    def get_name(self):
        """返回属性的标准名称"""
        pass


    #默认方法，若采用默认抽取，则将他们补全
    def get_extract_patterns(self) -> list:
        """
        返回属性特征模式的正则表达式列表
        若不用extract默认函数功能可不重写
        """
        return None

    def get_filter_patterns(self) -> list:
        """
        返回属性过滤模式的正则表达式列表
        若不用filter默认函数功能可不重写
        :return:
        """
        return None

    def get_name_patterns(self)-> list:
        """
        返回识别属性名称的正则表达式列表
        正则表达式列表具有先后顺序
        """
        return None

    #自定义方法
    def get_name_in_infobox(self,attributes):
        """
        寻找infobox属性名称列表中是否有该属性，是则返回该属性，不是返回None
        限定每个属性值对应infobox中的一个
        可自定义，默认为该方法
        """
        patterns=self.get_name_patterns() 
        if patterns is None:
            for attribute in attributes:
                if self.get_name() in attribute:return attribute
        else:
            for pattern in patterns:
                for attribute in attributes:
                    if re.search(pattern,attribute):return attribute

    def filter(self,s):
        """
        依照模式对属性值过滤
        :param s: 属性值字符串
        :return: 若识别出多个属性值，则返回列表，若只有一个属性值，则返回字符串，没有则返回None
        例：
            身高为167cm。 ——> 167cm
        """

        if s: 
            if self.get_filter_patterns():return get_first_pattern(self.get_filter_patterns(), s)
            else:return s

    def extract(self,s):
        """
        从一句话中抽出符合该属性特征的属性值，用于增加infobox
        先抽出模式，在进行过滤
        不考虑多个属性值，只抽一个属性值
        :param s: 句子
        :return: 属性值 或 None
        例：身高
            东京都出身，身长149cm，体重39kg，血型AB型 ——>身长149cm ——> 149cm

        在识别之前要全角转半角以防出现模式下识别错误
        """
        if not s: return None
        s = strB2Q(s)
        if self.get_extract_patterns():
            for pattern in self.get_extract_patterns():
                ret = re.search(pattern, s)
                if ret:
                    ret = self.filter(ret.group())
                    if ret: return ret

    def normalize(self,value_list):
        """对属性值列表做归一化，默认返回出现次数最多的"""
        return max(value_list,key=value_list.count)

    def equal(self,value1,value2):
        """判断两个属性值是否相等"""
      #  return value1==value2
        if value1 in value2:return True
        if value2 in value1:return True
        return False


    def print_statistics(self):
        """
        打印统计数据
        """
        print("属性：",self.get_name())
        print("统计结果：")
        print(self.statistics)

    def remote_supervision(self,item):
        """
        远程监督，详细介绍如下
        :param item:人物网页抽出来的4项
        :return:
            (属性值,属性值所在句子)，若句子为简介，则标识句子为"summary"，若没有，则返回None
            若属性值有多个，则返回元组列表
        """
        def search_value(self,value,item):
            """
            对属性值value进行搜索，范围为所有有效信息
            :param value: 属性值
            :param item: 4项
            :return: (属性值,属性值所在句子)，若句子为简介，则标识句子为"summary"，若没有，则返回None
            """
            if item["summary"] and value in item["summary"]:
                self.statistics["属性值在summary数量"]+=1
                return (value, "summary")
            else:
                if "para" in item.keys():
                    for i in item["para"]:
                        if value==i or len(i)<3:continue
                        if value in i:
                            if self.get_name()+"："!=i[:len(self.get_name()+"：")]:
                                self.statistics["属性值在para数量"] += 1
                                return (value, i)

        attribute_name=self.get_name_in_infobox(item["infobox"].keys())
        if attribute_name:
            self.statistics["识别出该属性数量"]+=1
            value = item["infobox"][attribute_name]
            value = self.filter(value)
            if value is None or value =="":
                self.statistics["无效属性值数量"] += 1
            elif isinstance(value,list):
                self.statistics["多属性值数量"]+=1
                result=[]
                for i in value:
                    search_pair=search_value(self,i,item)
                    if search_pair:result.append(search_pair)
                if result:return result
            else:
                res=search_value(self,value,item)
                if res:return res

        # 添加extract
        # if "summary" in item.keys():
        #     res=self.extract(item["summary"])
        #     if res:
        #         self.statistics["文中直接抽出属性值数量"]+=1
        #         self.statistics["属性值在summary数量"] += 1
        #         return (res, "summary")
        # if "para" in item.keys():
        #     for i in item["para"]:
        #         res = self.extract(i)
        #         if res and self.get_name()+"："!=i[:len(self.get_name()+"：")]:
        #             self.statistics["文中直接抽出属性值数量"] += 1
        #             self.statistics["属性值在para数量"] += 1
        #             return (res, i)

class Name(AttributeInterface):
    def __init__(self):
        super().__init__()

    def get_name(self):
        return "姓名"

    def get_name_patterns(self)-> list:
        return [
            "中文名|中文名称|姓名|名字"
        ]

    def normalize(self,value_list):
        """
        让子串相同的归为一类(如何实现)
        返回出现次数最多的
        """
        res = dict()
        for value in value_list:
            flag=True
            for res_value in res.keys():
                if value in res_value:
                    res[res_value] += 1
                    flag=False
                    break
                elif res_value in value:
                # 替换成更长的
                    res[value] = res[res_value]
                    del res[res_value]
                    flag=False
                    break
            if flag:res[value]=1
        return max(res.items(),key=lambda item:item[1])[0]
              
    def filter(self,s):
        特殊案例=[
            "曺政奭（朝鲜汉字）",
            "阚成友，男",
        ]
        if not s:return None
        if s==filter_chinese(s) :return s
        s=strQ2B(s)
        sep_notes=["(",")","/","、",","]
        for sep_note in sep_notes:
            s=s.replace(sep_note," ")
        s=s.split()
        s=[i for i in s if i!="" and i!=" "]
        if s:return s[0]

class BirthDate(AttributeInterface):
    def __init__(self):
        super().__init__()

    def get_name(self):return "出生日期"

    def get_extract_patterns(self) -> list:
        return [
            ".{4,12}(出生|生)",
            "(出生|生于).{4,12}",
            "（.{3,10}(-|—|~)"  # 后面至多匹配9个，至少匹配2个
        ]

    def get_filter_patterns(self) -> list:
        return [
            "(公元前|公元)[0-9一二三四五六七八九十零〇]+(年|年代|世纪)(初|前期|中期|后期|末期|末)*",              #前面带公元
            "[0-9一二三四五六七八九十零〇]+(年|\.)[0-9一二三四五六七八九十〇正如初元腊]+(月|\.)[0-9一二三四五六七八九十〇]+(日|号)",  # 某年某月某日
            "[0-9一二三四五六七八九十〇零]+(年|\.)[0-9一二三四五六七八九十〇]+(月)",  # 某年某月
            "[0-9]{4}(-|—)[0-9]+((-|—)[0-9]+)*", #年-月-日
            "[0-9一二三四五六七八九十〇零][0-9一二三四五六七八九十〇零][0-9一二三四五六七八九十〇零][0-9一二三四五六七八九十〇零]*(年)*",#某年
            "[0-9一二三四五六七八九十〇零上个]+(世纪)[0-9一二三四五六七八九十〇零]*(年|年代)(初|前期|中期|后期|末期|末)*", #世纪年代
            "[0-9一二三四五六七八九十〇零][十〇0零](年代)(初|前期|中期|后期|末期|末)*" #上个世纪的年代
        ]

    def get_name_patterns(self)-> list:
        return [
            "出生日期|出生年月|出生时间",
            "生日"
        ]

    def normalize(self,value_list):
        """
        先进行格式化（年，月，日）
        然后进行包含统计
        最后选出最多的那个
        """

        res=dict() #代表年、月、日
        value_list=[self.filter(value) for value in value_list]
        value_list=[value for value in value_list if value is not None]
        if not value_list:return None
        for value in value_list:
            format_value=tuple(re.findall("[0-9一二三四五六七八九十零〇]+",value)) #拆分出年月日
            if format_value and len(format_value)<4:
                flag=True
                for res_value in res.keys():
                    if res_value==format_value or res_value[:len(format_value)]==format_value:
                        res[res_value]+=1
                        flag=False
                        break
                    elif format_value[:len(res_value)]==res_value:
                        res[format_value]=res[res_value]+1
                        del res[res_value]
                        flag=False
                        break
                if flag:res[format_value]=1
        
        res=max(res.items(),key=lambda item:item[1])[0]
        if len(res)==1:return res[0]
        elif len(res)==2:return res[0]+"年"+res[1]+"月"
        else:return res[0]+"年"+res[1]+"月"+res[2]+"日"

    def equal(self,value1,value2):
        value1=tuple(re.findall("[0-9一二三四五六七八九十零〇]+",value1)) #拆分出年月日
        value2=tuple(re.findall("[0-9一二三四五六七八九十零〇]+",value2)) #拆分出年月日
        if value1[:len(value2)]==value2:return True
        if value2[:len(value1)]==value1:return True
        return False

class Country(AttributeInterface):

    def __init__(self):
        """
        国家没有固定模式，但是有预定义词表
        """
        super().__init__()
        vocab_file = "output/country_vocab.json"
        self.country_vocab = set(json.loads(open(vocab_file, encoding='utf-8').read()))  # 建立词表

        self.extract_patterns = [
            "(国籍：|国籍为|出生在|生于|，).{2,10}",  # 后面至多匹配9个，至少匹配2个
            ".{2,10}国籍"  # 前面匹配数量
        ]

    def get_name(self):return "国籍"

    def get_name_patterns(self)-> list:
        return [
            "国家|国籍"
        ]

    def filter(self, s):
        """
        若果出现多个国家，就返回列表，以尽可能多的标注为准
        """
        if filter_chinese(s) != s:  # 有分隔符或其它字符
            result = []
            for i in self.country_vocab:
                if i in s: result.append(i)
            if len(result) > 1: return result
            if len(result) == 1: return result[0]
        else:
            if len(s) > 1 and "的" not in s: return s

    def extract(self, s):
        """
        :param s:
        :param country_vocab:词表
        :return:国籍，若没有国籍则返回None
        """
        if not s: return None
        s = strB2Q(s)
        for pattern in self.extract_patterns:
            ret = re.search(pattern, s)
            if ret:
                ret = ret.group()
                for country in self.country_vocab:
                    if country in ret: return country
        # 在句子开头匹配
        for i in range(2, 9):
            if s[:i] in self.country_vocab: return s[:i]

        # 肯定为中国国籍的标志
        if re.search("中共党员|中国共产党|入党|书记|党委", s): return "中国"
      
class BirthPlace(AttributeInterface):
    def __init__(self):
        super().__init__()
        vocab_file = "output/birthplace_vocab.json"
        if os.path.exists(vocab_file):
            self.birthpalce_vocab = set(json.loads(open(vocab_file, encoding='utf-8').read()))  # 建立词表
        else:
            values = get_values("出生地|籍贯", "result2.json")
            new_values = []
            for value in values:
                value =self.filter(value)
                if value is not None and value !="":
                    new_values.append(value)
            self.birthpalce_vocab = set(create_value_vocab(new_values, vocab_file, limit_len=1))

        self.extract_patterns=[
            ".{0,15}(出生).{0,15}",
            "(生于).{2,10}",
            ".{2,10}人"
        ]

    def get_name(self):return "出生地"

    def get_name_patterns(self)-> list:
        return [
            "出生地",
            "籍贯",
            "祖籍"
        ]

    def filter(self,s):
        """
        嵌套问题如何解决？
        #可用词表，由小到大记录，识别时由小到大识别
        """
        if s!=filter_chinese(s):return None

        edge = ["生于", "生", "出生", "人"]
        for i in range(3, 0, -1):
            if s[:i] in edge: s = s[i:]
        for i in range(3, 0, -1):
            if s[-i:] in edge: s = s[:-i]
        return s

    def extract(self, s):
        """
        :param s:
        :param country_vocab:词表
        :return:国籍，若没有国籍则返回None

        可以抽多个
        """
        if not s: return None
        s = strB2Q(s)
        for pattern in self.extract_patterns:
            ret = re.search(pattern, s)
            if ret:
                ret = ret.group()
                for birthpalce in self.birthpalce_vocab:
                    if birthpalce in ret: return birthpalce

    def normalize(self,value_list):
        """
        让子串相同的归为一类
        返回该类中出现次数最多的，最长包含串
        判断的时候要查看是否包含子串
        """
        res = dict()
        for value in value_list:
            flag=True
            for res_value in res.keys():
                if value in res_value:
                    res[res_value] += 1
                    flag=False
                    break
                elif res_value in value:
                # 替换成更长的
                    res[value] = res[res_value]
                    del res[res_value]
                    flag=False
                    break
            if flag:res[value]=1
        return max(res.items(),key=lambda item:item[1])[0]

class School(AttributeInterface):

    """
    多属性值问题
    """
    def __init__(self):
        super().__init__()
        vocab_file = "output/school_vocab.json"
        if os.path.exists(vocab_file):
            self.school_vocab = set(json.loads(open(vocab_file, encoding='utf-8').read()))  # 建立词表
        else:
            values = get_values("毕业院校|毕业学校", "result2.json")
            new_values = []
            for value in values:
                value =self.filter(value)
                if value is not None and value !="":
                    if isinstance(value,list):
                        for i in value:new_values.append(i)
                    else:new_values.append(value)
            self.school_vocab = set(create_value_vocab(new_values, vocab_file, limit_len=1))

        self.extract_patterns=[
            ".{0,20}(毕业).{0,20}"
            ".{0,20}(学位|学历|专业).{0,20}"
        ]

    def get_name(self):return "毕业院校"

    def get_name_patterns(self)-> list:
        return [
            "毕业院校|毕业学校"
        ]

    def filter(self,s):
        """
        分开属性值
        必须两者都成立才能成为一个属性值、避免远距离实体出现
        :param s:
        :return:
        """

        def single_school_filter(s):
            # 有先后识别顺序
            """
            学校可能有多个
            有99.3%符合标准
            无法识别的情况
            1.学校简称：麻省理工 上海复旦 哈佛 南京中医药 县立北高 长影 上海二医 江南水师 长安县立第五高小
            2.似学校非学校：嵩山少林寺 南宁市体工队 中国人民银行研究生部 北京电影制片厂 中国美术家协会培训中心
            3.非学校：苏黎世综合技术联盟 天主教
            :param s:
            :return:
            """
            if s!=filter_chinese(s):return None
            patterns = [
                ".*(分校|学院|研究所)",  # 防止二级院校名丢失
                ".*(学校|学院|学堂|学园|大学|院校|研究所|实验室)",
                ".*(女中|初中|高中|附中|[0-9一二三四五六七八九十]+中|[0-9一二三四五六七八九十]+小)",
                ".*(学|院|校)",  # 小学|中学|
                ".*(大|专|师范|医科|班|堂|团|医药)"  # 研究院|书院|剧院|中科院|美术院|
                # 卫校|分校|军校|艺校|党校
                # 初中|高中|附中
                # 医科大 北大
            ]
            ret = None
            for pattern in patterns:
                ret = re.search(pattern, s)
                if ret:
                    s = ret.group()
                    if s[:3] == "毕业于": s = s[3:]
                    if s[:2] == "毕业": s = s[2:]
                    return s
            if not ret: return None

        sep_notes = "、，,"
        for sep_note in sep_notes:
            if sep_note in s:
                s = s.split(sep_note)
                break
        if isinstance(s,list):
            s = [single_school_filter(i) for i in s]
            s = [i for i in s if i is not None]
            return s[0] if len(s)==1 else s
        else:
            return single_school_filter(s)

    def extract(self, s):
        """
        :param s:
        :param country_vocab:词表
        :return:国籍，若没有国籍则返回None

        可以抽多个
        """
        if not s: return None
        s = strB2Q(s)
        for pattern in self.extract_patterns:
            ret = re.search(pattern, s)
            if ret:
                ret = ret.group()
                for school in self.school_vocab:
                    if school in ret: return school

    def normalize(self,value_list):
        """
        抽出出现次数最多的前几个
        """
        school_num=3
        value_list=[self.filter(value) for value in value_list]
        value_list=[value for value in value_list if value ]
        value_count=dict()
        for value in value_list:
            if isinstance(value,str):value_count[value]=value_count.get(value,0)+1
        value_count=[k[0] for k in sorted(value_count.items(),key=lambda item:item[1],reverse=True)]
        return value_count[:school_num]

class Nation(AttributeInterface):

    def __init__(self):
        super().__init__()
        """国籍也可以是民族"""
        vocab_file = "output/nation_vocab.json"
        if os.path.exists(vocab_file):
            self.nation_vocab = set(json.loads(open(vocab_file, encoding='utf-8').read()))  # 建立词表
        else:
            values=get_values("民族","result2.json")
            new_values=[]
            for value in values:
                if value is not None and value !="" and value!="族":
                    if value[-1] in "族人":value=value[:-1]
                new_values.append(value)
            self.nation_vocab=set(create_value_vocab(new_values,vocab_file,limit_len=1))

        self.extract_patterns = [
            "(民族).{2,10}",  # 后面至多匹配9个，至少匹配2个
            ".{2,10}族"  # 前面匹配数量
        ]

    def get_name(self):return "民族" 

    def filter(self, s):
        """
        将"族"去掉
        """
        s=filter_chinese(s)
        if not s:return None
        if len(s)==1:s=s+"族"
        if s[-1]!="族":return None
        return s

    def normalize(self,value_list):
        """
        只保留末尾有族的
        返回出现次数最多的
        """
        value_list=[value for value in value_list if value[-1]=="族"]
        if value_list:
            return max(value_list,key=value_list.count)


    def extract(self, s):
        """
        :param s:
        :param country_vocab:词表
        :return:国籍，若没有国籍则返回None
        """
        if not s: return None
        s = strB2Q(s)
        for pattern in self.extract_patterns:
            ret = re.search(pattern, s)
            if ret:
                ret = ret.group()
                for nation in self.nation_vocab:
                    if nation in ret: return nation
        # 在句子开头匹配
        for i in range(2, 9):
            if s[:i] in self.nation_vocab: return s[:i]

class Gender(AttributeInterface):

    def __init__(self):
        super().__init__()

    def get_name(self):return "性别"

    def get_extract_patterns(self) -> list:
        return [
            "(性别).{1,3}",
            "，(男|女)性{0,1}，",
        ]
        
    def get_filter_patterns(self) -> list:
        return [
            "(男|女)"
        ]
    
    def normalize(self,value_list):
        """只保留男女，并返回出现次数更多的"""
        value_list=[self.filter(value) for value in value_list]
        value_list=[value for value in value_list if value is not None]
        if value_list:
            res=max(value_list,key=value_list.count)
            return res

class ForeignName(AttributeInterface):
    def __init__(self):
        super().__init__()
    def get_name(self):
        return "外文名"
    def get_name_patterns(self)-> list:
        return [
            "外文名",
            "英文名"
        ]
    def filter(self,s):

        特殊案例=[
            "とうわエリオ罗马音:TouwaErio",
            "普什图文:MalālahYūsafzay,英文：MalalaYousafzai",
            "英语：MohammedDaoudKhan或者SardarMohammedDaoud",
            "SimonYam或YamTat-wah",
            "櫻井浩美（さくらいはるみ，SakuraiHarumi）",
            "キノガッサ、Breloom",
            "Athena·Dai",
            "相楽美佐枝（さがらみさえ）SagaraMisae",
            "문정희/Jeong-hieMun",
            "HwangMiHee(HuangMiHee/HangMiHee)",
            "St.LiuJOHNDingHan",
            "엄기준(UmKiJoon)"
        ]

        if not s :return None
        s=strQ2B(s)
        s=s.split(":")
        if len(s)>2:return None
        elif len(s)==2:s=s[1]
        else:s=s[0]

        sep_notes=["(",")","/","、","或者","或",","]
        for sep_note in sep_notes:
            s=s.replace(sep_note," ")
        s=s.split()
        s=[i for i in s if i!="" and i!=" "]
        if len(s)==1:return s[0]
        if s:return s

    def normalize(self,value_list):
        """
        让子串相同的归为一类(如何实现)
        返回出现次数最多的
        """
        res = dict()
        for value in value_list:
            flag=True
            for res_value in res.keys():
                if value in res_value:
                    res[res_value] += 1
                    flag=False
                    break
                elif res_value in value:
                # 替换成更长的
                    res[value] = res[res_value]
                    del res[res_value]
                    flag=False
                    break
            if flag:res[value]=1
        return max(res.items(),key=lambda item:item[1])[0]

class DeathDate(AttributeInterface):
    def __init__(self):
        super().__init__()

    def get_name(self):return "逝世日期"

    def get_name_patterns(self)->list:
        return [
            "逝世日期|死亡日期|死亡时间|逝世时间|去世时间"
        ]

    def get_extract_patterns(self) -> list:
        return [
            ".{4,12}(逝世|去世|离世)",
            "(死于).{4,12}",
            "(-|—|~).{3,10}）"# 后面至多匹配9个，至少匹配2个
        ]

    def get_filter_patterns(self) -> list:
        return [
            "(公元前|公元)[0-9一二三四五六七八九十零〇]+(年|年代|世纪)(初|前期|中期|后期|末期|末)*",              #前面带公元
            "[0-9一二三四五六七八九十零〇]+(年|\.)[0-9一二三四五六七八九十〇正如初元腊]+(月|\.)[0-9一二三四五六七八九十〇]+(日|号)",  # 某年某月某日
            "[0-9一二三四五六七八九十〇零]+(年|\.)[0-9一二三四五六七八九十〇]+(月)",  # 某年某月
            "[0-9]{4}(-|—)[0-9]+((-|—)[0-9]+)*", #年-月-日
            "[0-9一二三四五六七八九十〇零][0-9一二三四五六七八九十〇零][0-9一二三四五六七八九十〇零][0-9一二三四五六七八九十〇零]*(年)*",#某年
            "[0-9一二三四五六七八九十〇零上个]+(世纪)[0-9一二三四五六七八九十〇零]*(年|年代)(初|前期|中期|后期|末期|末)*", #世纪年代
            "[0-9一二三四五六七八九十〇零][十〇0零](年代)(初|前期|中期|后期|末期|末)*" #上个世纪的年代
        ]

    def normalize(self,value_list):
        """
        先进行格式化（年，月，日）
        然后进行包含统计
        最后选出最多的那个
        """

        res=dict() #代表年、月、日
        value_list=[self.filter(value) for value in value_list]
        value_list=[value for value in value_list if value is not None]
        if not value_list:return None
        for value in value_list:
            format_value=tuple(re.findall("[0-9一二三四五六七八九十零〇]+",value)) #拆分出年月日
            if format_value and len(format_value)<4:
                flag=True
                for res_value in res.keys():
                    if res_value==format_value or res_value[:len(format_value)]==format_value:
                        res[res_value]+=1
                        flag=False
                        break
                    elif format_value[:len(res_value)]==res_value:
                        res[format_value]=res[res_value]+1
                        del res[res_value]
                        flag=False
                        break
                if flag:res[format_value]=1
        res=max(res.items(),key=lambda item:item[1])[0]
        if len(res)==1:return res[0]
        elif len(res)==2:return res[0]+"年"+res[1]+"月"
        else:return res[0]+"年"+res[1]+"月"+res[2]+"日"

    def equal(self,value1,value2):
        value1=tuple(re.findall("[0-9一二三四五六七八九十零〇]+",value1)) #拆分出年月日
        value2=tuple(re.findall("[0-9一二三四五六七八九十零〇]+",value2)) #拆分出年月日
        if value1[:len(value2)]==value2:return True
        if value2[:len(value1)]==value1:return True
        return False

class SportType(AttributeInterface):
    def __init__(self):
        super().__init__()
    def get_name(self):
        return "运动项目"

    def filter(self,s):
        "与外文名类似"
        特殊案例=[
            "（田径）：400米",
            "田径（短跑：100米、200米、接力）",
        ]

        if not s :return None
        s=strQ2B(s)
        s=s.split(":")
        if len(s)>2:return None
        elif len(s)==2:s=s[1]
        else:s=s[0]
        sep_notes=["(",")","/","、","或者","或",","]
        for sep_note in sep_notes:
            s=s.replace(sep_note," ")
        s=s.split()
        s=[i for i in s if i!="" and i!=" "]
        if len(s)==1:return s[0]
        if s:return s

class Production(AttributeInterface):
    def __init__(self):
        super().__init__()
    def get_name(self):
        return "作品"
    def get_name_patterns(self)-> list:
        return [
            "代表作品",
            "登场作品",
            "主要作品"
        ]
    def filter(self,s):
        "标准：不加书名号，这样好识别"
        "这种属性在检查时只能用正确识别的概率"
        特殊案例=[
            "《十万个冷笑话》《罗小黑战记》《星游记》《古剑奇谭2》等",
            "《射雕英雄传》、《杨门女将》《十四女英豪》",
            "《机动新世纪高达X》蒂珐·亚迪尔、《银河天使》香草·亚修",
            "《田娟画集·人物卷",
            "荷花壶、牡丹壶、金瓜壶、菱形壶、南瓜烟缸",
            "寿在百岁外寿字，人生万福中福字，《龙》被奥运博物馆收藏",
            "《棋魂》进藤光、《AIR》神尾观铃、《Keroro军曹》日向冬树",
            "《外来媳妇本地郎》，《乘龙怪婿》",
            "歌曲:只是当时、蔷蔷、坏女孩、厚脸皮影视:蔷薇之恋、真命天女、就想赖着你、新天生一对",
            "万里长城，秦淮风华，猴神等",

        ]

        if not s :return None
        if "《" in s or "》" in s:
            s=re.findall("《.*?》",s)
            if s==[]:return None
            s=[i[1:-1] for i in s]
            if len(s)==1:s=s[0]

        else:
            s=s.rstrip("等")
            if s=="":return None
            sep_notes=["、",",","，",";"]
            for sep_note in sep_notes:
                s=s.replace(sep_note," ")
            s=s.split()
            s=[i for i in s if i!="" and i!=" "]
            if len(s)==1:return s[0]
            if s==[]:return None
        return s

    def normalize(self,value_list):
        """对属性值列表做归一化，默认返回出现次数最多的"""
        return list(set(value_list))

    def equal(self,value1,value2):
        """判断两个属性值是否相等"""
        return value1==value2


class SportTeam(AttributeInterface):
    def __init__(self):
        super().__init__()
    def get_name(self):
        return "所属运动队"

    def filter(self,s):
        "标准：不加书名号，这样好识别"
        "这种属性在检查时只能用正确识别的概率"
        #比较难搞
        #边界问题比较多，并且无法处理
        特殊案例=[
            "无",
            "已经退役，现任黑山足协主席",
             "新疆西域·君悦海棠足球队",
             "北京首钢,佛山能兴怡翠，山西中宇，辽宁盼盼，青岛双星",
             "国家队，北京女足",
              "1960－1972年效力博卡，替球队出阵389场，进9球。",
              "河床，瓦斯科达迦马",
              "沙尔克04足球俱乐部，瑞士国家队",
              "曾效力：维也纳快速足球俱乐部",
              "丹麦灵比：CSC队",
              "国家队：智利", #这种情况不会识别出来，如果是智力国家队则可以
        ]

        if not s :return None
        s=strQ2B(s)
        s=s.split(":")
        if len(s)>2:return None
        elif len(s)==2:s=s[1]
        else:s=s[0]

        sep_notes=["(",")","/","、",","]
        for sep_note in sep_notes:
            s=s.replace(sep_note," ")
        s=s.split()
        s=[i for i in s if i!="" and i!=" "]
        if len(s)==1:return s[0]
        if s:return s
        return s

class Height(AttributeInterface):
    def __init__(self):
        super().__init__()


    def get_name(self):return "身高"

    def get_name_patterns(self) ->list:
        return ["身高|身长"]

    def get_extract_patterns(self) -> list:
        return [
            "(身高|身长).{3,12}",  # 后面至多匹配9个，至少匹配2个
            # "(身高为|身高：|身高|身长|身高只有|身高仅有|身高体重).{3,10}",
        ]

    def get_filter_patterns(self) -> list:
        """
        经测评：有97.3%的数据符合要求
        不符合的特征：
        （1）非人类身高：53米、七万八千米
        （2）非精确描述：顶丈、不详、一丈多、？米
        （3）错误标签：足球、4350px、身形剽悍
        """
        return [
            "[0-9一二两三四五六七八九零十百.]+(cm|CM|Cm|cM|厘米|公分)",  # 限定单位为cm 例：172cm、一八零厘米
            "[1-2一二][0-9一二两三四五六七八九零][0-9一二两三四五六七八九零]",    #限定三位数字 例：172、一七三
            "[012](\.|．)[0-9]+(米|m|M)",                             #限定中间有小数点，且单位为m，例：1.8米
            "[零一二012](米|m|M)[0-9一二两三四五六七八九零]*",               #限定格式：数字+米+数字，例：1米5
            "[0-9一二两三四五六七八九](尺)[0-9一二两三四五六七八九]*(寸)*",      #限定格式：数字+尺+数字+寸（后两项可选）
            "[0-9一二两三四五六七八九](英尺)[0-9一二两三四五六七八九]*(英寸)*"    #限定格式：数字+英尺+数字+英寸（后两项可选）
        ]

class Weight(AttributeInterface):

    def __init__(self):
        super().__init__()

    def get_name(self):return "体重"

    def get_extract_patterns(self) -> list:
        return [
            "(体重|身高体重).{3,10}",  # 后面至多匹配9个，至少匹配2个
        ]

    def get_filter_patterns(self) -> list:
        """
        经测评：有90.9%的数据符合要求
        不符合的特征：
        （1）非人类体重：2万4千吨，40000吨
        （2）没有单位：66，67（假设体重不能没有单位）,该错误有三种 1.体重：[78] 2.体重：[78]kg 3.19[78]年生（占多数）
        （3）错误标签：赛艇、1990年7月4日，180cm
        """
        return [
            "[0-9一二两三四五六七八九零十百\.]+(kg|KG|Kg|kG|千克|公斤)",        # 限定单位为kg 例：65kg
            "[0-9一二两三四五六七八九零十百\.]+斤",                            # 限定单位为斤 例：
            "[0-9一二两三四五六七八九零十百\.]+磅",                            # 限定单位为磅，例：165磅
        ]

class Belief(AttributeInterface):
    def __init__(self):
        super().__init__()
    def get_name(self):
        return "信仰"
    def get_name_patterns(self)-> list:
        return [
            "信仰",
            "宗教信仰",
            "主要宗教"
        ]
    def filter(self,s):
        "标准：不加书名号，这样好识别"
        "这种属性在检查时只能用正确识别的概率"
        特殊案例=[
            "泛非主义、非洲民族主义、非洲社会主义",
            "儒学（今文经学）",
            "追逐梦想，勇敢面对",
        ]

        if not s :return None
        if s==filter_chinese(s):return s
    
    def normalize(self,value_list):
        value_list=[i for i in value_list if i!="无"]
        if value_list:
            return max(value_list,key=value_list.count)
        else : return []

class Degree(AttributeInterface):

    def __init__(self):
        super().__init__()
    def get_name(self):return "学历"

    def get_name_patterns(self)-> list:
        return [
            "学历",
            "学位",
            "文化程度",
            "学位学历"
        ]


    def get_name_in_infobox(self,attributes):
        for attribute in attributes:
            if re.search("学历|学位",attribute):return attribute

    def get_extract_patterns(self) -> list:
        return [
            ".{0,10}(学历|学位).{0,10}"
            #".{2,10}(毕业).{2,10}"，会包含学校
        ]
    def get_filter_patterns(self) -> list:
        
        """
        98.5%符合要求
        1.不是学位而是职称：教授、讲师、工程师、博导、研究员、进士
        2.错误：中共党员、贵阳医学院
        3.没说全：双学历
        """
        return [
            "(博士|本科|大专|硕士研究生|中专|学士|博士后|专科|EMBA|高中|初中|大本|中学|小学)",
            "(大学|硕士|研究生|MBA)",
            "(案首|监生|生员|禀生|贡生|举人|解元|进士|探花|榜眼|状元)",  #古代学历
            "(工学|理学)"
        ]

class PoliticsStatus(AttributeInterface):
    # 同样意义形式多变，先去掉
    def __init__(self):
        super().__init__()

    def get_name(self):
        return "政治面貌"


    #默认方法，若采用默认抽取，则将他们补全
    def get_extract_patterns(self) -> list:
        """
        返回属性特征模式的正则表达式列表
        若不用extract默认函数功能可不重写
        """
        return None

    def get_filter_patterns(self) -> list:
        """
        返回属性过滤模式的正则表达式列表
        若不用filter默认函数功能可不重写
        :return:
        """
        return None

class SportPosition(AttributeInterface):
    def __init__(self):
        super().__init__()

    def get_name(self):
        """返回属性的标准名称"""
        return "场上位置"

    #默认方法，若采用默认抽取，则将他们补全
    def filter(self,s):

        if not s :return None
        s=strQ2B(s)
        s=s.split(":")
        if len(s)>2:return None
        elif len(s)==2:s=s[1]
        else:s=s[0]

        sep_notes=["(",")","/","、",","]
        for sep_note in sep_notes:
            s=s.replace(sep_note," ")
        s=s.split()
        s=[i for i in s if i!="" and i!=" "]
        if len(s)==1:return s[0]
        if s:return s

class Constellation(AttributeInterface):
    def __init__(self):
        super().__init__()

    def get_name(self):
        """返回属性的标准名称"""
        return "星座"

    #默认方法，若采用默认抽取，则将他们补全
    def get_extract_patterns(self) -> list:
        return [".{2,3}星座.{2,3}"]
    def get_filter_patterns(self):
        return ["白羊","金牛","双子","巨蟹","狮子","处女","天秤","天蝎","人马","摩羯","宝瓶","双鱼","山羊","牧羊","射手","射手","水瓶","蛇夫","天平"]


def remote_supervision2(person_json,des_file,attribute_min_num=1):
    """
    对item进行过滤
    """
    file=open(person_json, 'r', encoding='utf-8')
    data = json.loads(file.read())
    file.close()
    new_data=[]
    for item in tqdm(data):
        new_item=dict()
        new_item["name"]=item["name"]
        new_item["summary"]=[item["summary"]] if item["summary"] else []
        new_item["infobox"]=dict()
        for attribute,value in item["infobox"].items():
            if item["summary"] and value in item["summary"]:new_item["infobox"][attribute]=value
            elif item["para"]:
                for para in item["para"]:
                    if value in para:
                        new_item["infobox"][attribute]=value
                        new_item["summary"].append(para)
                        break
        if len(new_item["infobox"])>=attribute_min_num:new_data.append(new_item)
    save_json(new_data,des_file)

def remote_supervision_para(person_json,des_json,min_attribute_num=4):
    """
    对item进行过滤,保留para的全貌
    """
    attributes=[
        #先前的属性
        Country(),Gender(),Height(),Weight(),Nation(),Degree(),School(),BirthPlace(),BirthDate(),DeathDate(),
        #后加的属性
        Name(),ForeignName(),SportType(),SportTeam(),Belief(),SportPosition(),PoliticsStatus(),Constellation(),Production()
    ]

    file=open(person_json, 'r', encoding='utf-8')
    data = json.loads(file.read())
    file.close()
    new_data=[]
    for item in tqdm(data):
        new_infobox=dict()
        for attribute in attributes:
            value_content=attribute.remote_supervision(item)
            if value_content:
                if isinstance(value_content,list):
                    value=[]
                    for i in value_content:
                        value.append(i[0])
                    new_infobox[attribute.get_name()] = value
                else:
                    new_infobox[attribute.get_name()]=value_content[0]
        if len(new_infobox)>=min_attribute_num:
            new_item=dict(item) 
            new_item["infobox"]=new_infobox
            new_data.append(new_item)
    new_data.sort(key=lambda item:len(item["infobox"]),reverse=True)
    save_json(new_data,des_json)

def remote_supervision(person_json,des_json):
    """
    对item进行过滤
    """
    attributes=[
        #先前的属性
        Country(),Gender(),Height(),Weight(),Nation(),Degree(),School(),BirthPlace(),BirthDate(),DeathDate(),
        #后加的属性
        Name(),ForeignName(),SportType(),SportTeam(),Belief(),SportPosition(),PoliticsStatus(),Constellation(),Production()
    ]

    file=open(person_json, 'r', encoding='utf-8')
    data = json.loads(file.read())
    file.close()
    new_data=[]
    for item in tqdm(data):
        introduction_para=set()
        new_infobox=dict()
        for attribute in attributes:
            value_content=attribute.remote_supervision(item)
            if value_content:
                if isinstance(value_content,list):
                    value=[]
                    for i in value_content:
                        if i[1] != "summary":
                            introduction_para.add(i[1])
                        value.append(i[0])
                    new_infobox[attribute.get_name()] = value
                else:
                    if value_content[1]!="summary":
                        introduction_para.add(value_content[1])
                    new_infobox[attribute.get_name()]=value_content[0]
        introduction_para=list(introduction_para)
        new_summary = [item["summary"]]+introduction_para
        new_summary=[filter_line(i) for i in new_summary if filter_line(i)is not None]

        if new_infobox and new_summary:

            for value in new_infobox.values():
                if not value:print("value hehe")
            for summ in new_summary:
                if not new_summary:print("summary hehe")

            new_data.append({"name":item["name"],"infobox":new_infobox,"summary":new_summary})

    for attribute in attributes:
        attribute.print_statistics()
    save_json(new_data,des_json)

def extract_person_attribute(source_file_list,des_json,attribute_min_num=2):
    """
    抽取出人物的实体
    source_file：所有实体文件
    attribute_min_num:最小属性数量
    return：列表
    """
    res=[]
    for source_file in source_file_list:
        with open(source_file,'r',encoding="utf-8")as file:
            data=json.loads(file.read())

        attributes=[        #先前的属性
            Country(),Gender(),Height(),Weight(),Nation(),Degree(),School(),BirthPlace(),BirthDate(),DeathDate(),
            #后加的属性
            Name(),ForeignName(),SportType(),Production(),SportTeam(),SportPosition(),Constellation()
            ]
        new_data=[]
        print(len(data))
        for item in data:
            if not item:print("hehe")
            attribute_num=0
            for attribute in attributes:
                if item["infobox"]and item["summary"]:
                    if attribute.get_name_in_infobox(item["infobox"].keys()):attribute_num+=1
            if attribute_num>=attribute_min_num:new_data.append(item)
        res+=new_data
    save_json(res,des_json)

def extract_person_high(source_file_list,des_json,attribute_min_num=5):
    """
    抽取出人物的实体
    source_file：所有实体文件
    attribute_min_num:最小属性数量
    return：列表
    """
    res=[]
    for source_file in source_file_list:
        with open(source_file,'r',encoding="utf-8")as file:
            data=json.loads(file.read())

        attributes=[        #先前的属性
            Country(),Gender(),Height(),Weight(),Nation(),Degree(),School(),BirthPlace(),BirthDate(),DeathDate(),
            #后加的属性
            Name(),ForeignName(),SportType(),SportTeam(),SportPosition(),Belief()
            ]
        new_data=[]
        for item in tqdm(data):
            new_item=dict(item)
            new_item["infobox"]=dict()
            attribute_num=0
            for attribute in attributes:
                if item["infobox"]and item["summary"]:
                    attribute_name=attribute.get_name_in_infobox(item["infobox"].keys())
                    if attribute_name:
                        attribute_num+=1
                        new_item["infobox"][attribute.get_name()]=item["infobox"][attribute_name]
            if attribute_num>=attribute_min_num:new_data.append(new_item)
        res+=new_data
    res.sort(key=lambda item:len(item["infobox"]),reverse=True)

    save_json(res,des_json)

def process_remote_data(remote_json,des_json):
    """
    对特定属性再次处理
    单个字符属性值问题：民族、性别、血型  #已添加
    身高体重日期，属性表没有单位属性值有单位 #已添加
    太短的冒号太多，星座明显 :已添加
    #信仰因共产党问题说法不一
    #场上位置可以建立词表
    #星座有座的话更准确，对于某些词语可能不准确
    需要缩短句长
    按顺序出现属性值

    此外还需要判断这句话是否为一个正常的句子

    两种操作：
        修改item操作
        item排序
    """
    data=get_json_data(remote_json)
    def summary_attribute(item):
        """让特定属性只在summary中出现"""
        attributes = [Gender()]
        for attribute in attributes:
            if attribute.get_name() in item["infobox"].keys():
                value=item["infobox"][attribute.get_name()]
                if value not in item["summary"]:del item["infobox"][attribute.get_name()]

    def implement_attribute(item):
        """格式补全"""
        attributes=[Height(),Weight(),BirthDate(),DeathDate()]
        for attribute in attributes:
            if attribute.get_name() in item["infobox"]:
                value=item["infobox"][attribute.get_name()]
                item["infobox"][attribute.get_name()]=strQ2B(value)  #全部转化为半角
                for line in item["summary"]:
                    if value in line:
                        value2=attribute.filter(re.search(value+".{0,7}",line).group())
                        if value2.split("-")!=2:value=value2
                        item["infobox"][attribute.get_name()]=value
                        break

    def remove_same_item(data):
        new_data=[]
        person_set=set()
        for item in data:
            if item["name"] not in person_set:
                person_set.add(item["name"])
                new_data.append(item)
        return new_data

    def sort_data(data):
        # 按照infobox的质量对其打分
        """
        按照infobox的质量对其打分
        包括：
            让更多的属性在上面
            让更多稀有的属性在上面 属性占比倒数之和
            让句长尽量分布均匀
        :param data:
        :return:
        """
        info = get_remote_json_info(remote_json)

        #取中位数句长
        mid_count = 0
        mid_sentence_len=0
        for k, v in info["句长分布"].items():
            mid_count += v
            if mid_count > info["条目数"] / 2:
                mid_sentence_len = k
                break

        for item in data:
            score=0
            for attribute in item["infobox"].keys():
                score+=info["条目数"]/info["属性分布"][attribute]
                score+=len(item["infobox"])/sum([len(i) for i in item["summary"]])*10

            item["score"]=score

        data.sort(key=lambda item:item["score"],reverse=True)


    data=[item for item in data if item["summary"] is not None]

    for i in range(len(data)):
        implement_attribute(data[i])
    data=[item for item in data if len(item["infobox"])>2]
    #sort_data(data)
    data=remove_same_item(data)
    save_json(data,des_json)

def evaluate_two_infobox(json_file,des_file):
    """
    从抽取的list中获取重要的信息
    出现次数最多的，出现最长的，第一次出现的，所有出现的集合
    TP:正确识别
    FP:在predict，不在gold
    FN:在gold，不在predict

    对于每一个属性：
        TP：
    """    
    attributes=[
        #先前的属性
        Country(),Gender(),Height(),Weight(),Nation(),Degree(),School(),BirthPlace(),BirthDate(),DeathDate(),
        #后加的属性
        Name(),ForeignName(),SportType(),SportTeam(),Belief(),SportPosition()
    ]

    result_data=[]

    # gold_count,predict_count,right_count
    attribute_count={
        attribute.get_name():{"gold_count":0,"predict_count":0,"right_count":0,"exist_count":0} for attribute in attributes
    }





    data=get_json_data(json_file)
    for item in data:
        predict=item["predict"]
        gold=item["gold"]
        #转换数据格式：{name:{predict:[],gold:[]}}
        for attribute in attributes:
            gold_value=None
            predict_value=None
            if attribute.get_name() in gold.keys():
                gold_value=gold[attribute.get_name()]
                if not isinstance(gold_value,list):gold_value=[gold_value]
                attribute_count[attribute.get_name()]["gold_count"]+=len(gold_value)

            if attribute.get_name() in predict.keys():
                predict_value=predict[attribute.get_name()]
                predict_value=[i for i in predict_value if i]
                if predict_value:predict_value=attribute.normalize(predict_value)
                if predict_value:
                    if isinstance(predict_value,str):predict_value=[predict_value]
                    attribute_count[attribute.get_name()]["predict_count"]+=len(predict_value)

            # 预测有单实际没有的不算
            

            if gold_value and predict_value:
                attribute_count[attribute.get_name()]["exist_count"]+=len(predict_value)
                for i in gold_value:
                    for j in predict_value:
                        if attribute.equal(i,j):
                            attribute_count[attribute.get_name()]["right_count"]+=1
                        else:result_data.append([i,j])
    
    def format_num(num):
        return str(int(num*10000)/100)+"%"
    for i in attribute_count:
        if attribute_count[i]["right_count"]==0:
            attribute_count[i]["P"],attribute_count[i]["R"],attribute_count[i]["F"]=-1,-1,-1
        else:
            attribute_count[i]["P"]=attribute_count[i]["right_count"]/attribute_count[i]["gold_count"]
            attribute_count[i]["R"]=attribute_count[i]["right_count"]/attribute_count[i]["predict_count"]
            attribute_count[i]["R2"]=attribute_count[i]["right_count"]/attribute_count[i]["exist_count"]
            attribute_count[i]["F"]=2*attribute_count[i]["P"]*attribute_count[i]["R"]/(attribute_count[i]["P"]+attribute_count[i]["R"])
            attribute_count[i]["F2"]=2*attribute_count[i]["P"]*attribute_count[i]["R2"]/(attribute_count[i]["P"]+attribute_count[i]["R2"])
            
            attribute_count[i]["P"]=format_num(attribute_count[i]["P"])
            attribute_count[i]["R"]=format_num(attribute_count[i]["R"])
            attribute_count[i]["R2"]=format_num(attribute_count[i]["R2"])
            attribute_count[i]["F"]=format_num(attribute_count[i]["F"])
            attribute_count[i]["F2"]=format_num(attribute_count[i]["F2"])
        print(i,attribute_count[i])

    save_json(result_data,des_file)
    return attribute_count

def make_remote_data_para():
    #造全部人物介绍数据
    total_person="output/extract_info/person_data3.json"
    remote_supervision_result="output/attribute_19_result_para.json"
    remote_supervision_result_process="output/remote_supervision_result_process_para.json"
   # remote_supervision_para(total_person,remote_supervision_result)
    process_remote_data(remote_supervision_result,remote_supervision_result_process)

def make_remote_data():
    #造只包含不是人物介绍的数据
    total_person="output/extract_info/person_data3.json"
    remote_supervision_result="output/attribute_17_result.json"
    remote_supervision_result_process="output/remote_supervision_result_process.json"
    remote_supervision_result_process_cut="output/remote_supervision_result_process_cut.json"
    mrc_BIO_file="output/BIO_output/mrc"
    lstm_BIO_file="output/BIO_output/bio"
    remote_supervision(total_person,remote_supervision_result)
    process_remote_data(remote_supervision_result,remote_supervision_result_process)
    cut_json_data(remote_supervision_result_process,remote_supervision_result_process_cut,1000,41000)
    json2mrc(remote_supervision_result_process_cut,mrc_BIO_file)
    json2BIO(remote_supervision_result_process_cut,lstm_BIO_file)



# make_remote_data()
# make_remote_data_para()
# evaluate_two_infobox("output/model_output/dev_output_para_crf.json","output/model_output/dev_output_para_crf_result.json")
# save_json(output,"output/evaluate_two_infobox_result.json")
# data2excel(output,"output/dev_output_para.xlsx",mode="dict2")
# get_remote_json_info("output/remote_supervision_result_process.json")
# get_remote_json_info("output/remote_supervision_result_process_para.json")

