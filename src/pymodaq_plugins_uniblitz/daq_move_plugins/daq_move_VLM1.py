from pymodaq.daq_move.utility_classes import DAQ_Move_base  # base class
from pymodaq.daq_move.utility_classes import comon_parameters, main  # common set of parameters for all actuators
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo  # object used to send info back to the main thread
from pymodaq.daq_utils import daq_utils as utils
from easydict import EasyDict as edict  # type of dict
import serial
from serial.tools import list_ports

logger = utils.set_logger(utils.get_module_name(__file__))

class DAQ_Move_VLM1(DAQ_Move_base):
    """
        Wrapper object to access the Mock fonctionnalities, similar wrapper for all controllers.

        =============== ==============
        **Attributes**    **Type**
        *params*          dictionnary
        =============== ==============
    """
    _controller_units = 'whatever'
    is_multiaxes = False  # set to True if this plugin is controlled for a multiaxis controller (with a unique communication link)
    stage_names = []  # "list of strings of the multiaxes

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

    params = [   
        {
            'title': 'COM Port:',
            'name': 'COM_port',
            'type': 'list',
            'limits': COMports,
            'value': COMport
        },
        ## TODO for your custom plugin
                 # elements to be added here as dicts in order to control your custom stage
                 ############
                 {'title': 'MultiAxes:', 'name': 'multiaxes', 'type': 'group', 'visible': is_multiaxes, 'children': [
                     {'title': 'is Multiaxes:', 'name': 'ismultiaxes', 'type': 'bool', 'value': is_multiaxes,
                      'default': False},
                     {'title': 'Status:', 'name': 'multi_status', 'type': 'list', 'value': 'Master',
                      'limits': ['Master', 'Slave']},
                     {'title': 'Axis:', 'name': 'axis', 'type': 'list', 'limits': stage_names},

                 ]}] + comon_parameters

    def __init__(self, parent=None, params_state=None):
        """
            Initialize the the class

            ============== ================================================ ==========================================================================================
            **Parameters**  **Type**                                         **Description**

            *parent*        Caller object of this plugin                    see DAQ_Move_main.DAQ_Move_stage
            *params_state*  list of dicts                                   saved state of the plugins parameters list
            ============== ================================================ ==========================================================================================

        """
        super().__init__(parent, params_state)
        self.controller = None
        self.settings.child(('epsilon')).setValue(1)
        self.settings.child('bounds', 'is_bounds').setValue(True)
        self.settings.child('bounds', 'max_bound').setValue(1)
        self.settings.child('bounds', 'min_bound').setValue(0)

    def check_position(self):
        """Get the current position from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        pos = self.current_position
        self.emit_status(ThreadCommand('check_position',[pos]))

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
        controller: (object) custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

        Returns
        -------
        self.status (edict): with initialization status: three fields:
            * info (str)
            * controller (object) initialized controller
            *initialized: (bool): False if initialization failed otherwise True
        """

        try:
            # initialize the stage and its controller status
            # controller is an object that may be passed to other instances of DAQ_Move_Mock in case
            # of one controller controlling multiactuators (or detector)

            self.status.update(edict(info="", controller=None, initialized=False))

            # check whether this stage is controlled by a multiaxe controller (to be defined for each plugin)
            # if multiaxes then init the controller here if Master state otherwise use external controller
            if self.settings.child('multiaxes', 'ismultiaxes').value() and self.settings.child('multiaxes',
                                   'multi_status').value() == "Slave":
                if controller is None:
                    raise Exception('no controller has been defined externally while this axe is a slave one')
                else:
                    self.controller = controller
            else:
                com_port = self.settings.child('COM_port').value()
                self.controller = serial.Serial(com_port, baudrate=9600)
                logger.info('Shutter connected on port '+com_port)

            self.status.info = "Port ouvert"
            self.status.controller = self.controller
            self.status.initialized = True
            return self.status

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status',[getLineInfo()+ str(e),'log']))
            self.status.info=getLineInfo()+ str(e)
            self.status.initialized=False
            return self.status


    def move_Abs(self, position):
        """ Move the actuator to the absolute target defined by position

        Parameters
        ----------
        position: (flaot) value of the absolute target positioning
        """
        if position not in [0, 1]:
            position = 1
        self.controller.write([b'A', b'@'][int(position)])
        self.current_position = int(position)

    def move_Rel(self, position):
        """ Move the actuator to the relative target actuator value defined by position

        Parameters
        ----------
        position: (flaot) value of the relative target positioning
        """
        if position != 0:
            self.move_Abs(int(not self.current_position))

    def move_Home(self):
        """
          Send the update status thread command.
            See Also
            --------
            daq_utils.ThreadCommand
        """
        self.move_Abs(0)
        self.current_position = 0


if __name__ == '__main__':
    # main(__file__)
    test = DAQ_Move_VLM1()
    print(test.params)
    test.ini_stage()
    test.move_Abs(0)
    test.close()
