# coding=cp1251
import urllib
import urllib2
import cookielib
import re
import datetime
import string
import message
import common

class Diesel:
    __cookies = cookielib.CookieJar()
    __opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(__cookies))
    __opener.addheaders=[('User-agent', 'Mozilla/5.0')]
    __lastUserPageDataId = -1
    __lastUserPageData = ''
    __lastUserPageDataDateTime = datetime.datetime(1, 1, 1)
    __timeThreshold = 600
    #
    # private methods
    #
    def __init__(self):
        self.__opener.open('http://diesel.elcat.kg')

    def __getUserBirthDateById(self, userId):
        monthes = {}
        monthes[u'Янв'] = 1
        monthes[u'Фев'] = 2
        monthes[u'Март'] = 3
        monthes[u'Апр'] = 4
        monthes[u'Май'] = 5
        monthes[u'Июнь'] = 6
        monthes[u'Июль'] = 7
        monthes[u'Авг'] = 8
        monthes[u'Сен'] = 9
        monthes[u'Окт'] = 10
        monthes[u'Ноя'] = 11
        monthes[u'Дек'] = 12
        data = self.__getUserPageDataById(userId)

        if data == None:
            return None
        elif data.count(u'Возраст не указан') > 0:
            return None
        else:
            result = re.search(u'<span id=\'pp-entry-born-text\'>(.+?)</span>', data)
            datestr = result.groups(1)
            result = re.search('(.+)-(.+)-(.+)', datestr[0])

            year = int(result.group(3))
            month = monthes[result.group(1)]
            day = int(result.group(2))
            date = datetime.date(year, month, day)
            return date

    def __setRatingById(self, userId, rating):
        data = self.__getUserPageDataById(userId, True)

        if data == None:
            return None

        pattern = 'var ipb_md5_check         = "(.+?)";'
        result = re.search(pattern, data)
        md5_check = result.group(1)

        url = 'http://diesel.elcat.kg/index.php?s=&act=xmlout&do=member-rate&member_id=%s&rating=%s&md5check=%s' % (
        str(userId), str(rating), str(md5_check))
        response = self.__opener.open(url)
        return response.read()

    def __getUserPageDataById(self, userId, update=False):
        if userId == self.__lastUserPageDataId and \
                        (self.__lastUserPageDataDateTime.now() - \
                                 self.__lastUserPageDataDateTime).total_seconds() < \
                        self.__timeThreshold and not update:
            data = self.__lastUserPageData
        else:
            url = 'http://diesel.elcat.kg/index.php?showuser=' + str(userId)
            response = self.__opener.open(url)
            data = response.read().decode('cp1251')
            self.__lastUserPageDataId = userId
            self.__lastUserPageData = data
            self.__lastUserPageDataDateTime = self.__lastUserPageDataDateTime.now()

            if response.geturl() == 'http://diesel.elcat.kg/index.php':
                data = None

        return data

    def __getUserGroupById(self, userId):
        data = self.__getUserPageDataById(userId)

        if data == None:
            return None

        pattern = u'<!-- MAIN TABLE -->[\W\S]+?<strong>([\W\S]+?)</strong>'
        result = re.search(pattern, data)

        if result == None:
            return None
        else:
            return result.group(1)

    def __getUserEntryDataByName(self, userName):
        if not isinstance(userName, basestring):
            return None

        userNameCoded = userName.encode('cp1251')
        name_data = urllib.urlencode({'name': userNameCoded})
        response = self.__opener.open('http://diesel.elcat.kg/index.php?act=members&name_box=begins', name_data)
        data = response.read().decode('cp1251')

        pattern = '<!-- Entry for ' + re.escape(userName)
        pattern += '([\W\S]+?)'
        pattern += '<!-- End of Entry -->'

        result = re.search(pattern, data)

        if result == None:
            return None
        else:
            return result.group(1)

    def __getUserMessagesById(self, userId, top):
        response = self.__opener.open('http://diesel.elcat.kg/index.php?act=Search&CODE=getalluser&mid=' + str(userId))
        url = response.geturl()

        m = 0
        p = 0
        result = []
        for pp in range(10 ^ 20):
            url2 = url + '&st=' + str(pp * 25)
            response = self.__opener.open(url2)
            data = response.read().decode('cp1251')
            ind = string.find(data, '<div class="borderwrap">')

            pattern = u'<div class="borderwrap">[\W\S]+?'
            pattern += u'showtopic=([\d]+?)&[\W\S]+?'
            pattern += u'<div id="post-member-([\d]+?)"[\W\S]+?'
            pattern += u'Отправлено: ([\W\S]+?)</span>[\W\S]+?'
            pattern += u'<div class="postcolor"[\W\S]+?>([\W\S]+?)'
            pattern += u' <!--IBF.ATTACHMENT'
            r = re.finditer(pattern, data)
            for mm in r:
                mmm = message.Message()
                mmm.Id = mm.group(2)
                mmm.Theme = mm.group(1)
                mmm.DateTime = common.DieselDateToDatetime(mm.group(3))
                mmm.Text = mm.group(4)

                result.append(mmm)
                m = m + 1
                if m >= top:
                    break
            if m >= top:
                break
        return result

    def __FindVarIpb(self, url):
        result = re.search('var ipb_md5_check.+=.+"(.+)";', url)
        return result.group(1)

    def __GetPostID(self, url):
        result = re.findall('<!--Begin Msg Number\s+(.+)-->', url)
        return str(result[1])

    #
    # public methods
    #
    def IsLogin(self):
        response = self.__opener.open('http://diesel.elcat.kg')
        data = response.read().decode('cp1251')
        if data.count('http://diesel.elcat.kg/index.php?act=Login&amp;CODE=03') > 0:
            return True
        else:
            return False


    def GetUserBirthDate(self, user):
        if isinstance(user, int):
            return self.__getUserBirthDateById(user)
        elif isinstance(user, basestring):
            return self.__getUserBirthDateById(self.__getUserBirthDateByName(user))
        else:
            return None


    def GetIdByName(self, userName):
        data = self.__getUserEntryDataByName(userName)

        if data == None:
            return None

        pattern = 'http://diesel\.elcat\.kg/index\.php\?showuser=(.+?)\"'
        result = re.search(pattern, data)

        if result == None:
            return 0
        else:
            return int(result.group(1))


    def GetNameById(self, userId):
        data = self.__getUserPageDataById(userId)

        if data == None:
            return None

        pattern = u'<title>(.+?) - Просмотр профиля</title>'
        result = re.search(pattern, data)
        return result.group(1)


    def UnLogin(self):
        response = self.__opener.open('http://diesel.elcat.kg')
        data = response.read().decode('cp1251')

        pattern = u'http://diesel\.elcat\.kg/index\.php\?act=Login&amp;CODE=03&amp;k=(.+?)">Выход'
        result = re.search(pattern, data)

        if result != None:
            self.__opener.open('http://diesel.elcat.kg/index.php?act=Login&CODE=03&k=' + result.group(1))


    def SetRating(self, user, rating):
        if isinstance(user, int):
            return self.__setRatingById(user, rating)
        elif isinstance(user, basestring):
            return self.__setRatingById(self.GetIdByName(user), rating)
        else:
            return None


    def Login(self, login, password, privacy=True):
        if privacy:
            login_data = urllib.urlencode({'UserName': login, 'PassWord': password, 'Privacy': 'checked'})
        else:
            login_data = urllib.urlencode({'UserName': login, 'PassWord': password})
        self.__opener.open('http://diesel.elcat.kg/index.php?act=Login&CODE=01&CookieDate=1', login_data)


    def GetUserGroup(self, user):
        if isinstance(user, int):
            return self.__getUserGroupById(user)
        elif isinstance(user, basestring):
            return self.__getUserGroupById(self.GetIdByName(user))
        else:
            return None

    def GetMessages(self, user, top=10 ^ 5):
        if isinstance(user, int):
            return self.__getUserMessagesById(user, top)
        elif isinstance(user, basestring):
            return self.__getUserMessagesById(self.GetIdByName(user), top)
        else:
            return None


    def DeleteUserMessagesById(self, messageId):
        response = self.__opener.open('http://diesel.elcat.kg/index.php?showtopic=' + str(messageId))
        url = response.read()
        url = 'http://diesel.elcat.kg/index.php?act=Mod&CODE=04&f=409&t='+str(messageId)+'&p='+ self.__GetPostID(url)+'&st=0'+'&auth_key='+self.__FindVarIpb(url)
        self.__opener.open(url)



    def PostUserMessagesById(self, messageId):
        response = self.__opener.open('http://diesel.elcat.kg/index.php?showtopic=' + str(messageId))
        url = 'http://diesel.elcat.kg/index.php?act=Post&CODE=03&f=409&t='+str(messageId)+'&st=0'+'&auth_key='+self.__FindVarIpb(response.read())
        post_data = urllib.urlencode({'Post':'Up'})
        req = urllib2.Request(url, post_data)
        self.__opener.open(req)
