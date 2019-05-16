import message_queue as mq

class HaasoscopeStateMachine(object):
    """docstring for HaasoscopeStateMachine"""
    def __init__(self, gui, ser):
        super(HaasoscopeStateMachine, self).__init__()
        self.gui = gui
        self.ser = ser
        self.mq_adapter = mq.Adapter('main_queue')
        self.mq_subscriber = mq.Subscriber(self.mq_adapter)
        self.dologicanalyzer = False

    def togglelogicanalyzer(self):
        self.dologicanalyzer = not self.dologicanalyzer
        self.ser.setlogicanalyzer(self.dologicanalyzer)
        self.gui.setlogicanalyzer(self.dologicanalyzer)
        print(("dologicanalyzer is now",self.dologicanalyzer))

    def process_queue(self):
        while True:
            message = self.mq_subscriber.consume()
            if not message: break
            message_content = message.get_content_body()
            msg_id = message_content['id']
            print ("message id:", msg_id)
            if msg_id==1:
                ydata = message_content['ydata']
                bn = message_content['bn']
                self.gui.on_running(ydata, bn)
            elif msg_id==2:
                self.gui.drawtext()
            elif msg_id==3:
                self.togglelogicanalyzer()

        pass
