from tkinter import *
import message_queue as mq

class App:

    def __init__(self, master):

        frame = Frame(master)
        frame.pack()

        self.button = Button(
            frame, text="QUIT", fg="red", command=frame.quit
            )
        self.button.pack(side=LEFT)

        self.hi_there = Button(frame, text="Hello", command=self.say_hi)
        self.hi_there.pack(side=LEFT)

    def say_hi(self):
        print ("hi there, everyone!")

adapter1 = mq.Adapter('queue1')
adapter2 = mq.Adapter('queue1')

subscriber = mq.Subscriber(adapter1)

publisher = mq.Publisher(adapter2)

message_to_send = mq.Message({
    'id': 12345,
    'message': 'test publish'
    })

publisher.publish(message_to_send)
message_content = subscriber.consume().get_content_body()
print ("message id:", message_content['id'])
message = subscriber.consume()
if (message):
    message_content = message.get_content_body()
    print ("message id:", message_content['id'])

publisher.publish(message_to_send)
message = subscriber.consume()
if (message):
    message_content = message.get_content_body()
    print ("message id:", message_content['id'])

root = Tk()


app = App(root)

root.mainloop()
root.destroy() # optional; see description below