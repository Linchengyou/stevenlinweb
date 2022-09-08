from flask import render_template, redirect, url_for, request, Blueprint, jsonify
from flask_babel import _, lazy_gettext as _l
from app.form import QCForm
from config import web_QC_path, service_name
import os
import subprocess
import app.lib.network_interface as net_interface

qc_blueprint = Blueprint('qc', __name__)


@qc_blueprint.route('/devicetest/device_test.php', methods=['GET'])
def qc_old():
    """
    舊QC網址重新導向
    """
    return redirect(url_for('qc.qc'))


@qc_blueprint.route('/QC', methods=['GET'])
def qc():
    """
    QC測試網頁
    """
    form = QCForm()
    device_info = {}
    interface_dict = net_interface.get_network_interface_info()
    device_info['mac'] = interface_dict['mac']
    return render_template('qc.html', title=_l('QC Test'), form=form, data=device_info)


@qc_blueprint.route('/QC/proc', methods=['GET'])
def qc_proc():
    """
    QC測試流程
    """
    test_program = 'testpi_flask.py'  # 執行測試
    clear_program = 'clear_reg.py'   # 清空紀錄
    do_type = request.args.get('do_type')
    # 檢查測試程式是否運行中
    if do_type == 'check':
        cmd = "sudo ps -ef |grep '{}' | grep -v 'grep' | wc -l".format(test_program)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        outwithoutreturn = out.decode('utf-8').rstrip('\n')
        if outwithoutreturn == "0":
            pg_status = "stop"
        else:
            pg_status = "run"
        return jsonify(result=pg_status)
    # 中止測試程式
    elif do_type == 'end':
        os.system("sudo pkill -f {}{}".format(web_QC_path, test_program))
        os.system("sudo python3 {}{}".format(web_QC_path, clear_program))
        os.system("sudo systemctl start {}".format(service_name))
        return '', 204
    # 取得測試結果
    elif do_type == 'get_resp':
        file_path = web_QC_path + 'response.txt'
        with open(file_path, 'r') as f:
            return f.read()
    # 取得版本號
    elif do_type == 'get_version':
        file_path = web_QC_path + 'response_version.txt'
        with open(file_path, 'r') as f:
            return f.read()
    # 啟動測試程式
    else:
        os.system("sudo systemctl stop {}".format(service_name))
        cmd = "sudo ps -ef |grep '{}' | grep -v 'grep' | wc -l".format(test_program)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        outwithoutreturn = out.decode('utf-8').rstrip('\n')
        # 檢核測試程式是否已啟動，若未啟動才執行
        if outwithoutreturn == "0":
            subprocess.Popen("sudo python3 {}{}".format(web_QC_path, test_program), shell=True)
        return '', 204
