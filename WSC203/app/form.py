from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, PasswordField, IntegerField, BooleanField
from wtforms.widgets import Input, PasswordInput
from wtforms.validators import DataRequired, IPAddress, NumberRange
from flask_babel import _, lazy_gettext as _l
import app.lib.config_lib as config_lib
import SocketClient_WSC203_8888_copy as SCW8
import json

class ButtonInput(Input):
    """
    用來顯示 input type='button' 按鈕的元件(widget)
    """
    input_type = 'button'

    def __call__(self, field, **kwargs):
        kwargs.setdefault('value', field.label.text)
        return super(ButtonInput, self).__call__(field, **kwargs)


class ButtonInputField(BooleanField):
    """
    input type='button'式按钮
    """
    widget = ButtonInput()


class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    submit = SubmitField(_l('Sign In'))


class NetworkForm(FlaskForm):
    network_type = SelectField(id='network_type', label='Network Configuration',
                               coerce=int, choices=[(1, 'DHCP'), (2, 'Static')],
                               validators=[])
    mac_address = StringField(id='mac', label='MAC Address')
    ip_address = StringField(id='ip', label='IP Address', validators=[DataRequired(), IPAddress()])
    netmask = StringField(id='netmask', label='Netmask', validators=[DataRequired(), IPAddress()])
    gateway = StringField(id='gateway', label='Gateway', validators=[DataRequired(), IPAddress()])
    dns_server = StringField(id='dns', label='DNS Server', validators=[DataRequired(), IPAddress()])
    submit = SubmitField(_l('Apply'))


class SerialForm(FlaskForm):
    config = config_lib.Config().get_config()
    config_protocol = config['mcu']['mode']
    config_baud_rate = config['mcu']['baud_rate']
    protocol_list = ['Modbus', 'D-Bus']
    protocol = SelectField(id='protocol',
                           label=_l('Communication Protocol'),
                           coerce=int,
                           choices=[(index, data) for index, data in enumerate(protocol_list)],
                           # choices=[(x, x) for x in protocol_list],
                           default=config_protocol - 1,
                           validators=[])

    # baud_dict = {0: 1200, 1: 2400, 2: 4800, 3: 9600, 5: 19200, 6: 38400}
    baud_list = [1200, 2400, 4800, 9600, 19200, 38400]
    baud_rate = SelectField(id='baud_rate',
                            label=_l('Baud Rate'),
                            coerce=int,
                            choices=[(data, data) for data in baud_list],
                            default=config_baud_rate,
                            validators=[])
    timeout = IntegerField(id='timeout', label=_l('Timeout ( 10~10000 ms)'),
                           validators=[NumberRange(min=10, max=10000)])
    submit = SubmitField(_l('Apply'))


class ServerForm(FlaskForm):
    config = config_lib.Config().get_config()
    config_mode = config['setting']['oper_mode']
    mode_list = ['TCP-Server', 'TCP-Client']
    config_modbus_type = config['setting']['modbus_type']
    mode = SelectField(id='mode',
                       label=_l('Device Mode'),
                       coerce=int,
                       choices=[(index, data) for index, data in enumerate(mode_list)],
                       default=config_mode,
                       validators=[])
    port = IntegerField(id='port', label=_l('Port'), validators=[NumberRange(min=81, max=65535)])
    modbus_type_list = ['Modbus/RTU', 'Modbus/TCP']
    modbus_type = SelectField(id='modbus_type',
                              label=_l('Modbus Type'),
                              coerce=int,
                              choices=[(index, data) for index, data in enumerate(modbus_type_list)],
                              default=config_modbus_type,
                              validators=[])
    max_conn = SelectField(id='max_conn',
                           label=_l('Max Connection'),
                           coerce=int,
                           choices=[(index, data) for index, data in enumerate([1, 2, 3, 4])],
                           default=config_modbus_type,
                           validators=[])
    # inactivity_time = IntegerField(id='inactivity_time', label=_l('Inactivity Time (0~3600s)'),
    #                                validators=[NumberRange(min=0, max=3600)])
    tcp_alive_check_time = IntegerField(id='tcp_alive_check_time', label=_l('TCP Alive Check Time (0~20 min)'),
                                        validators=[NumberRange(min=0, max=20)])
    submit = SubmitField(_l('Apply'))
class TestForm(FlaskForm):
    data = json.loads(SCW8.run())
    V= data[0]['V']
    kWh =data[0]['kWh']
    kVArh =data[0]['kVArh']
class ClientForm(FlaskForm):
    config = config_lib.Config().get_config()
    config_mode = config['setting']['oper_mode']
    mode_list = ['TCP-Server', 'TCP-Client']
    mode = SelectField(id='mode',
                       label=_l('Device Mode'),
                       coerce=int,
                       choices=[(index, data) for index, data in enumerate(mode_list)],
                       default=config_mode,
                       validators=[])
    target_ip = StringField(id='target_ip', label=_l('Target IP Address'), validators=[DataRequired(), IPAddress()])
    target_port = IntegerField(id='target_port', label=_l('Target Port'),
                               validators=[DataRequired(), NumberRange(min=0, max=65535)])
    target_timeout = IntegerField(id='target_timeout', label=_l('Timeout (0~60s)'),
                                  validators=[NumberRange(min=0, max=60)])
    submit = SubmitField(_l('Apply'))


class QCForm(FlaskForm):
    btn_start = ButtonInputField(label=_l('啟動測試程式'))
    btn_stop = ButtonInputField(label=_l('停止測試程式'))


class ProfileForm(FlaskForm):
    new_pwd = StringField(id='new_pwd',
                          label=_l('New Password'),
                          widget=PasswordInput(hide_value=True),
                          validators=[DataRequired()])
    pwd_confirm = StringField(id='pwd_confirm',
                              label=_l('Confirm Password'),
                              widget=PasswordInput(hide_value=True),
                              validators=[DataRequired()])
    submit = SubmitField(_l('Modify'))


class PasswordResetForm(FlaskForm):
    submit = SubmitField(_l('Password Reset'))
