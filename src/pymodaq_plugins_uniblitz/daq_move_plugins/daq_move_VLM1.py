from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuatorType,\
    DataActuator  # common set of parameters for all actuators
from pymodaq.utils.daq_utils import ThreadCommand # object used to send info back to the main thread
from pymodaq.utils.parameter import Parameter
import serial
from serial.tools import list_ports



class DAQ_Move_VLM1(DAQ_Move_base):

    _controller_units = 'whatever'
    is_multiaxes = False

    _axis_names = ['Axis1', 'Axis2']  # TODO for your plugin: complete the list
    _epsilon = 0.1
    data_actuator_type = DataActuatorType['DataActuator']  # wether you use the new data style for actuator otherwise set this
    # as  DataActuatorType['float']  (or entirely remove the line)

    COMports = [COMport.device for COMport in list_ports.comports()]
    isOpened = False
    button = False

    if len(COMports) > 0:
        if 'COM10' in COMports:
            COMport = 'COM10'
        else:
            COMport = COMports[0]
    else:
        COMport = None
    stage_names = []

    params = [   
        {
            'title': 'COM Port:',
            'name': 'COM_port',
            'type': 'list',
            'limits': COMports,
            'value': COMport
        },
                 ] + comon_parameters_fun(is_multiaxes, stage_names)

    def __init__(self, parent=None, params_state=None):
        super().__init__(parent, params_state)
        self.controller = None
        self.settings.child(('epsilon')).setValue(1)
        self.settings.child('bounds', 'is_bounds').setValue(True)
        self.settings.child('bounds', 'max_bound').setValue(1)
        self.settings.child('bounds', 'min_bound').setValue(0)
        self.current_position = 0

    def get_actuator_value(self):
        """Not implemented yet.
        """
        pos = self.current_position     #The position it remembers, but does not check with the hardware.
        return pos

    def close(self):
        """
        Terminate the communication protocol
        """
        if self.controller is not None:
            self.controller.close()

    def commit_settings(self, param):
        """
            | Activate any parameter changes on the PI_GCS2 hardware.
            |
            | Called after a param_tree_changed signal from DAQ_Move_main.

        """

        if param.name() == "COM_Port":
            self.close()
        else:
            pass

    def ini_stage(self, controller=None):
        """Actuator communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        try:
            com_port = self.settings.child('COM_port').value()
            self.controller = serial.Serial(com_port, baudrate=9600)
            # logger.info('Shutter connected on port '+com_port)


            info = "Port ouvert"
            initialized = True
            return info, initialized
        except Exception as e:
            info = 'Initialisation failed'
            initialized = False
            return info, initialized

    def move_abs(self, value: DataActuator):
        if value > 0:
            value = 1
        else:
            value = 0
        self.controller.write([b'A', b'@'][int(value)])
        self.current_position = int(value)

    def move_rel(self, value: DataActuator):
        if value != 0:
            self.move_abs(int(not self.current_position))

    def move_home(self):
        """Call the reference method of the controller"""
        self.move_abs(0)
        self.current_position = 0



if __name__ == '__main__':
    # main(__file__)
    test = DAQ_Move_VLM1()
    print(test.params)
    test.ini_stage()
    test.move_abs(0)
    test.close()
