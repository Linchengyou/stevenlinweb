from flask import render_template, flash, redirect, url_for, request, session, Blueprint, g
from flask_babel import _, lazy_gettext as _l
from flask_login import login_required
from app.form import NetworkForm, SerialForm, ServerForm, ClientForm,TestForm
import app.lib.config_lib as config_lib
from config import web_app_lib_path, service_name, product_info_path, app_lib_path
import subprocess
import app.lib.network_interface as net_interface
import json
import pathlib
import sys

# 取得不同python專案之lib路徑
sys.path.append(app_lib_path)
from db_lib_action import get_action_tmp

func_blueprint = Blueprint('func', __name__)


@func_blueprint.route('/network', methods=['GET', 'POST'])
@login_required
def network_setting():
    """
    網路設定頁面
    """
    form = NetworkForm()
    if form.validate_on_submit():
        if form.network_type.data == 1:
            # DHCP
            print('DHCP')
            subprocess.Popen('sudo python3 {}network.py dhcp'.format(web_app_lib_path), shell=True)
        else:
            # Static
            print('Static')
            subprocess.Popen(
                'sudo python3 {}network.py static {} {} {} {}'.format(web_app_lib_path, form.ip_address.data,
                                                                      form.netmask.data, form.gateway.data,
                                                                      form.dns_server.data), shell=True)
        subprocess.Popen('sudo systemctl restart gateway-ssdp.service', shell=True)
        flash(_l('Success!'), 'alert-success')
        return redirect(url_for('func.network_setting'))
        # return redirect('http://{}:5000{}'.format(form.ip_address.data, url_for('func.network_setting')), 301)
    else:
        interface_dict = net_interface.get_network_interface_info()
        form.mac_address.data = interface_dict['mac']
        form.ip_address.data = interface_dict['ip']
        form.netmask.data = interface_dict['netmask']
        form.gateway.data = interface_dict['gateway']
        if net_interface.get_network_type():
            form.network_type.data = 1
        else:
            form.network_type.data = 2
        form.dns_server.data = net_interface.get_dns_server(interface_dict['name'])[0]
    return render_template('network_setting.html', title='Network Setting', form=form)


@func_blueprint.route('/serial', methods=['GET', 'POST'])
@login_required
def serial_setting():
    # Serial設定頁面
    form = SerialForm()
    config = config_lib.Config().get_config()
    config_protocol = config['mcu']['mode']
    # config_baud_rate = config['mcu']['baud_rate']
    if config['mcu']['mode'] == 1:
        config_baud_rate = config['uart']['uart1']['baudrate']
        config_timeout = config['uart']['uart1']['timeout']
    else:
        config_baud_rate = config['mcu']['baud_rate']
        config_timeout = config['uart']['uart2']['timeout']
    config_tcp_mode = config['setting']['oper_mode']
    if form.validate_on_submit():
        config = config_lib.Config().get_config()
        if g.user.username == 'dae':
            if config['mcu']['mode'] != form.protocol.data + 1:
                config['mcu']['mode'] = form.protocol.data + 1
                # 產品型號切換 modbus WSC203, D-bus CC2100-v3.0
                product_info = json.loads(pathlib.Path(product_info_path).read_text())
                if config['mcu']['mode'] == 1:
                    product_info['model']['type'] = "WSC"
                    product_info['model']['number'] = "203"
                    product_info['model']['name'] = "WSC203"
                else:
                    product_info['model']['type'] = "CC"
                    product_info['model']['number'] = "2100-v3.0"
                    product_info['model']['name'] = "CC2100-v3.0"
                with open(product_info_path, 'w') as f:
                    json.dump(product_info, f, indent=2)
                subprocess.Popen('sudo systemctl restart multicast', shell=True)

        if config['mcu']['mode'] == 1:
            config['uart']['uart1']['baudrate'] = form.baud_rate.data
            config['uart']['uart1']['timeout'] = form.timeout.data / 1000
        else:
            config['mcu']['baud_rate'] = form.baud_rate.data
            config['uart']['uart2']['timeout'] = form.timeout.data / 1000

        config_lib.Config().update_config(config)
        # 非同步式重啟服務
        subprocess.Popen('sudo systemctl restart {}'.format(service_name), shell=True)
        flash(_l('Success!'), 'alert-success')
        return redirect(url_for('func.serial_setting'))
    else:
        if form.errors:
            flash_errors(form)
        else:
            form.protocol.process_data(config_protocol - 1)
            form.baud_rate.process_data(config_baud_rate)
            form.timeout.process_data(int(config_timeout * 1000))

    return render_template('serial_setting.html', title=_l('Serial Setting'), form=form, tcp_mode=config_tcp_mode)


@func_blueprint.route('/server', methods=['GET', 'POST'])
@login_required
def server_setting():
    select_mode = request.args.get('mode', type=int)
    config = config_lib.Config().get_config()
    config_mode = config['setting']['oper_mode']
    config_target_ip = config['setting']['target_ip']
    config_target_port = config['setting']['target_port']
    config_target_timeout = config['setting']['target_timeout']
    config_port = config['setting']['port']
    config_modbus_type = config['setting']['modbus_type']
    config_max_conn = config['setting']['max_conn']
    # config_inactivity_time = config['setting']['inactivity_time']
    config_tcp_alive_check_time = config['setting']['tcp_alive_check_time']
    if select_mode is None:
        select_mode = config_mode

    if select_mode == 0:
        """
        TCP Server Mode
        """
        form = ServerForm()

        if form.validate_on_submit():
            config = config_lib.Config().get_config()
            config['setting']['oper_mode'] = form.mode.data
            config['setting']['port'] = form.port.data
            config['mcu']['z_config'] = 1  # mcu master
            config['setting']['modbus_type'] = form.modbus_type.data
            if config['mcu']['mode'] == 1:
                config['setting']['max_conn'] = form.max_conn.data + 1
            # config['setting']['inactivity_time'] = form.inactivity_time.data
            config['setting']['tcp_alive_check_time'] = form.tcp_alive_check_time.data
            config_lib.Config().update_config(config)
            # 非同步式重啟服務
            subprocess.Popen('sudo systemctl restart {}'.format(service_name), shell=True)
            flash(_l('Success!'), 'alert-success')
            return redirect(url_for('func.server_setting'))
        else:
            if form.errors:
                flash_errors(form)
            else:
                form.mode.process_data(select_mode)
                form.port.process_data(config_port)
                form.modbus_type.process_data(config_modbus_type)
                if config['mcu']['mode'] == 1:
                    form.max_conn.process_data(config_max_conn - 1)
                # form.inactivity_time.process_data(int(config_inactivity_time))
                form.tcp_alive_check_time.process_data(int(config_tcp_alive_check_time))
        return render_template('device_setting_server.html', title=_l('Device Setting'), form=form,
                               mode=config['mcu']['mode'])
    else:
        """
        TCP Client Mode
        """
        form = ClientForm()
        if form.validate_on_submit():
            config = config_lib.Config().get_config()
            config['setting']['oper_mode'] = form.mode.data
            config['setting']['target_ip'] = form.target_ip.data
            config['setting']['target_port'] = form.target_port.data
            config['setting']['target_timeout'] = form.target_timeout.data
            config['mcu']['z_config'] = 5  # mcu slave
            config_lib.Config().update_config(config)
            # 非同步式重啟服務
            subprocess.Popen('sudo systemctl restart {}'.format(service_name), shell=True)
            flash(_l('Success!'), 'alert-success')
            return redirect(url_for('func.server_setting'))
        else:
            if form.errors:
                flash_errors(form)
            else:
                form.mode.process_data(select_mode)
                form.target_ip.process_data(config_target_ip)
                form.target_port.process_data(config_target_port)
                form.target_timeout.process_data(config_target_timeout)
        return render_template('device_setting_client.html', title=_l('Device Setting'), form=form)


@func_blueprint.route('/get_conn_status', methods=['GET'])
def get_conn_status():
    resp = get_action_tmp()
    if resp:
        if resp['conn_status'] == 0:
            output = '未連線'
        elif resp['conn_status'] == 1:
            output = '連線中...'
        elif resp['conn_status'] == 2:
            output = '連線成功'
        else:
            output = '連線失敗'
    else:
        output = '設備異常'
    return output


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash("{} 欄位錯誤 - {}".format(getattr(form, field).label.text, error), 'alert-danger')


@func_blueprint.route('/lang')
def lang_setting():
    """
    語系設定頁面
    """
    lang_key = request.args.get('lang_key', 1, type=str)
    lang_value = request.args.get('lang_value', 1, type=str)
    session['lang_key'] = lang_key
    session['lang_value'] = lang_value
    return redirect(request.referrer)

#測試
@func_blueprint.route('/test_setting', methods=['GET', 'POST'])
@login_required
def test_setting():
    # test設定頁面

    form = TestForm()


    return render_template('test_setting.html', title=_l('test Setting'), form=form)


