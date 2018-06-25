#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-06-25
# @Modify  : HuangYeWuDeng (https://github.com/ihacklog/VeryNginx)
# @Author  : Alexa (AlexaZhou@163.com)
# @Link    : https://github.com/alexazhou/VeryNginx
# @Disc    : install VeryNginx
# @Disc    : support python 2.x and 3.x

import os
import sys
import getopt
import filecmp
import string
import multiprocessing

openresty_pkg_url = 'https://openresty.org/download/openresty-1.13.6.2.tar.gz'
openresty_pkg = 'openresty-1.13.6.2.tar.gz'
ps_pkg_url = 'https://github.com/apache/incubator-pagespeed-ngx/archive/v1.13.35.2-stable.tar.gz'
ps_pkg_extract_dir = 'incubator-pagespeed-ngx-1.13.35.2-stable'
ps_pkg = 'v1.13.35.2-stable.tar.gz'
downloader_cmd='aria2c --allow-overwrite=true -c --file-allocation=none ' \
               '--log-level=error -m3 -s16 -x16 --max-file-not-found=3 -k1M ' \
               '--no-conf -Rtrue --summary-interval=0 -t10 --check-certificate=false'

work_path = os.getcwd()

dir_path = os.path.dirname(os.path.realpath(__file__))

def install_openresty( ):
    #check if the old version of VeryNginx installed( use upcase directory )
    if os.path.exists('/opt/VeryNginx/VeryNginx') == True:
        print("Seems that a old version of VeryNginx was installed in /opt/verynginx/...\n" \
              "Before install, please delete it and backup the configs if you need.")
        sys.exit(1)
    
    #makesure the dir is clean
    print('### makesure the work directory is clean')
    exec_sys_cmd('rm -rf {pkg_name}', pkg_name=openresty_pkg.replace('.tar.gz',''))
    
    #download openresty
    down_flag = True
    if os.path.exists( './' + openresty_pkg ):
        ans = ''
        while ans not in ['y','n']:
            ans = common_input(' Found %s in current directory, use it?(y/n)'%openresty_pkg)
        if ans == 'y':
            down_flag = False

    if down_flag == True:
        print('### start download openresty package...')
        exec_sys_cmd('rm -rf {file}', file=openresty_pkg)
        download_file(openresty_pkg_url, openresty_pkg)
        if exec_sys_cmd( 'test -s '+ ps_pkg, allow_fail=True) != True:
            download_file(ps_pkg_url, ps_pkg)
        if exec_sys_cmd('test -d ' + ps_pkg_extract_dir, allow_fail=True) != True:
            exec_sys_cmd( 'tar xvzf ' + ps_pkg)
        exec_sys_cmd( 'cd {ps_pkg_extract_dir} && ' \
                      'psol_url=$(scripts/format_binary_url.sh PSOL_BINARY_URL) &&'\
                      ' {downloader_cmd} $psol_url && tar -xzvf $(basename $psol_url) &&'\
                      ' cd ../'.format(ps_pkg_extract_dir=ps_pkg_extract_dir, downloader_cmd=downloader_cmd) )
        exec_sys_cmd( 'test -d ngx-fancyindex || git clone https://github.com/aperezdc/ngx-fancyindex.git')
    else:
        print('### use local openresty package...')
    
    print('### release the package ...')
    exec_sys_cmd( 'tar -xzf ' + openresty_pkg )
    exec_sys_cmd( 'tar -xzf ' + ps_pkg )

    #configure && compile && install openresty
    print('### configure openresty ...')
    os.chdir( openresty_pkg.replace('.tar.gz','') )
    exec_sys_cmd( './configure --prefix=/opt/verynginx/openresty' \
                  ' --user=nginx' \
                  ' --group=nginx' \
                  ' --with-http_v2_module' \
                  ' --with-http_sub_module' \
                  ' --with-http_stub_status_module' \
                  ' --with-luajit' \
                  ' --add-module={ps_ngx_module_dir}' \
                  ' --add-module={fancyindex_ngx_module_dir}',
                  ps_ngx_module_dir= dir_path+ "/" + ps_pkg_extract_dir,
                  fancyindex_ngx_module_dir= dir_path + "/ngx-fancyindex")
    
    print('### compile openresty ...')
    exec_sys_cmd( 'make -j{cpu_count}', cpu_count=multiprocessing.cpu_count()+1)
    
    print('### install openresty ...')
    exec_sys_cmd( 'make install' )

def install_verynginx():
    
    #install VeryNginx file
    print('### copy VeryNginx files ...')
    os.chdir( work_path )
    if os.path.exists('/opt/verynginx/') == False:
        exec_sys_cmd( 'mkdir -p /opt/verynginx' )
    
    exec_sys_cmd( 'cp -r -f ./verynginx /opt/verynginx' )

    #copy nginx config file to openresty
    if os.path.exists('/opt/verynginx/openresty') == True:
        if filecmp.cmp( '/opt/verynginx/openresty/nginx/conf/nginx.conf',
                        '/opt/verynginx/openresty/nginx/conf/nginx.conf.default', False ) == True:
            print('cp nginx config file to openresty')
            exec_sys_cmd( 'cp -f ./nginx.conf  /opt/verynginx/openresty/nginx/conf/' )
    else:
        print( 'openresty not fount, so not copy nginx.conf' )

    #set mask for the path which used for save configs
    exec_sys_cmd( 'chmod -R 777 /opt/verynginx/verynginx/configs' )


def update_verynginx():
    install_verynginx()    

def exec_sys_cmd(cmdStr, *args, **kwargs):
    accept_failed = False
    if 'allow_fail' in kwargs:
        accept_failed = kwargs.pop('allow_fail')
    cmd = string.Formatter().vformat(cmdStr, args, kwargs)
    print( cmd )
    ret = os.system( cmd )
    if  ret == 0:
        return ret
    else:
        if accept_failed == False:
            print('*** The installing stopped because something was wrong')
            exit(1)
        else:
            return False

def get_download_cmd(url, savename = ''):
    cmd = downloader_cmd + " -o {savename} {url}".format(url=url, savename=savename)
    return cmd

def download_file(url, savename = ''):
    cmd = get_download_cmd(url, savename)
    print (cmd)
    ret = os.system(cmd)
    return ret

def common_input( s ):
    if sys.version_info.major == 3:
        return input( s )
    else:
        return raw_input( s )

def safe_pop(l):
    if len(l) == 0:
        return None
    else:
        return l.pop(0)

def show_help_and_exit():
    help_doc = 'usage: install.py <cmd> <args> ... \n\n\
install cmds and args:\n\
    install\n\
        all        :  install verynginx and openresty(default)\n\
        openresty  :  install openresty\n\
        verynginx  :  install verynginx\n\
    update\n\
        verynginx  :  update the installed verynginx\n\
    '
    print(help_doc)
    exit()


if __name__ == '__main__':

    opts, args = getopt.getopt(sys.argv[1:], '', []) 
  
    cmd = safe_pop(args)
    if cmd == 'install':
        cmd = safe_pop(args)
        if cmd == 'all' or cmd == None:
            install_openresty()
            install_verynginx()
        elif cmd == 'openresty':
            install_openresty()
        elif cmd == 'verynginx':
            install_verynginx()
        else:
            show_help_and_exit()
    elif cmd == 'update':
        cmd = safe_pop(args)
        if cmd == 'verynginx':
            update_verynginx()
        else:
            show_help_and_exit()
    else:
        show_help_and_exit()

    print('*** All work finished successfully, enjoy it~')


else:
    print ('install.py had been imported as a module')
