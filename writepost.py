import sys
import time

localtime=time.localtime(time.time())
year = str(localtime.tm_year)
mon = str(localtime.tm_mon)
day = str(localtime.tm_mday)

if len(mon) == 1:
    mon = '0'+mon

fileday = year+'-'+mon+'-'+day+'-'

option = sys.argv[1]
mdformat = {
    'published':'true',
    'title':'',
    'series':'',
    'categories':'',
    'tags':'',
    'layout':'post',
    'excerpt':'',
    'comments':'yes',
    'toc':'true'
}

if option == '-c':
    filename = fileday+sys.argv[2]
    with open('_posts/'+filename+'.markdown', 'w')as f:
        f.write('---\n')
        for key in mdformat.keys():
            mdf = key+': '+mdformat[key]+'\n'
            f.write(mdf)
        f.write('---\n')

