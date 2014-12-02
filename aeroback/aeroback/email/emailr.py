import os
import smtplib
import email
from email import encoders

#-----------------------------------------------------------------------
from aeroback.abstractions.a_model import A_Model
from aeroback.abstractions.a_state import A_State
import aeroback.diagnostics.diagnostics as _D

import aeroback.constants.corestr as corestr

'''
Email module:
- sends plain or multipart email
'''


#-----------------------------------------------------------------------
# Model
#-----------------------------------------------------------------------
class Model(A_Model):

    def __init__(self):
        super(Model, self).__init__()

        self.active = None
        self.smtp_server = None
        self.smtp_port = None
        self.user = None
        self.password = None

    def debug_vars(self):
        if self.password:
            pwd = corestr._STR_PASSWORD_HIDDEN
        else:
            pwd = corestr._STR_PASSWORD_NOT_SET
        return [
            'active', self.active,
            'smtp_server', self.smtp_server,
            'smtp_port', self.smtp_port,
            'user', self.user,
            'password', pwd
            ]


#-----------------------------------------------------------------------
# State
#-----------------------------------------------------------------------
class State(A_State):

    def __init__(self, model):
        super(State, self).__init__()
        self.model = model
        self.sender = None
        self.recipient = None
        self.subject = None
        self.messages = None
        self.attachments = None

    def debug_vars(self):
        msgs = {}
        if self.messages:
            for key in self.messages:
                msg = "{}...".format(
                        ' '.
                        join(self.messages[key][:60].replace('\n', '').split()))
                msgs[key] = msg

        return [
            'sender', self.sender,
            'recipient', self.recipient,
            'subject', self.subject,
            'messages (extract)', msgs,
            'attachments', self.attachments
            ]


#-----------------------------------------------------------------------
# Sends email
#-----------------------------------------------------------------------
def _send(state, msg):
    if not state.model.active:
        _D.WARNING(
                __name__,
                "Email: sending not active, skipping"
                )
        return

    _D.DEBUG(__name__, "Email: sending...")

    if state.model.smtp_port is '25':
        _D.DEBUG(__name__, "Email: sending via port 25")
        mailer = smtplib.SMTP(
            state.model.smtp_server, state.model.smtp_port)

    elif state.model.smtp_port is '465':
        _D.DEBUG(__name__, "Email: sending via port 465")
        mailer = smtplib.SMTP_SSL(
            state.model.smtp_server, state.model.smtp_port)
    else:
        _D.DEBUG(__name__, "Email: sending via unspecified port, defaulting to 465")
        state.model.smtp_port = '465'
        mailer = smtplib.SMTP_SSL(
            state.model.smtp_server, state.model.smtp_port)

    try:
        mailer.login(state.model.user, state.model.password)
        mailer.sendmail(state.sender, [state.recipient], msg.as_string())

    except smtplib.SMTPException as ex:
        _D.ERROR(__name__, ex)

    finally:
        mailer.quit()
        _D.DEBUG(__name__, "Email: sending DONE")


#-----------------------------------------------------------------------
# Add attachments
#-----------------------------------------------------------------------
def _add_attachments(state, msg):
    if not state.attachments:
        return

    for afile in state.attachments:
        attachment = email.MIMEBase.MIMEBase('text', 'plain')
        attachment.set_payload(open(afile).read())
        attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(afile))
        encoders.encode_base64(attachment)
        msg.attach(attachment)


#-----------------------------------------------------------------------
# Sends email as a multipart
#-----------------------------------------------------------------------
def _build_multipart(state, message_html, message_plain):
    '''
    Build multipart email.
    '''

    # Build multipart msg
    if not message_plain:
        message_plain = "Plain text alternative not provided"

    msg = email.MIMEMultipart.MIMEMultipart('alternative')

    msg.add_header('From', state.sender)
    msg.add_header('To', state.recipient)
    msg.add_header('Subject', state.subject)

    part_text = email.MIMEText.MIMEText(message_plain, 'plain')
    msg.attach(part_text)
    part_html = email.MIMEText.MIMEText(message_html, 'html')
    msg.attach(part_html)

    return msg


#-----------------------------------------------------------------------
# Sends email as a plain
#-----------------------------------------------------------------------
def _build_plain(state, message_plain):
    '''
    Build plain email.
    '''
    msg = email.MIMEText.MIMEText(message_plain)
    msg['From'] = state.sender
    msg['To'] = state.recipient
    msg['Subject'] = state.subject

    return msg


#-----------------------------------------------------------------------
# Execute Wrapper
#-----------------------------------------------------------------------
def _execute(state):
    # Plain or multipart ?
    message_html = state.messages.get('text/html', None)
    message_plain = state.messages.get('text/plain', None)

    if message_html:
        msg = _build_multipart(state, message_html, message_plain)
    elif message_plain:
        msg = _build_plain(state, message_plain)
    else:
        err = 1
        msg = "No relevant message MIME type provided. Accepted text/html, text/plain"
        return err, msg

    # Optional attachements
    _add_attachments(state, msg)

    # Send
    _send(state, msg)

    return 0, None


#-----------------------------------------------------------------------
# Initialize model
#-----------------------------------------------------------------------
def _init_model(params):
    model = Model()

    err = 0
    msgs = []

    active = params.get('active', None)
    if active in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'certainly', 'uh-huh']:
        model.active = True
    elif active in ['false', '0', 'f', 'n', 'no', 'nope']:
        model.active = False
    else:
        msgs.append('active (true or false)')

    model.smtp_server = params.get('smtp_server', None)
    if not model.smtp_server:
        msgs.append('smtp_server')

    model.smtp_port = params.get('smtp_port', None)
    if not model.smtp_port:
        msgs.append('smtp_port')

    model.user = params.get('user', None)
    if not model.user:
        msgs.append('user')

    model.password = params.get('password', None)
    if not model.password:
        msgs.append('password')

    if msgs:
        err = 1
        msgs.insert(0, "Email model has missing params:")

    return model, err, ', '.join(msgs)


#-----------------------------------------------------------------------
# Initialize state
#-----------------------------------------------------------------------
def _init_state(model, params):
    state = State(model)
    return state, 0, None


#-----------------------------------------------------------------------
# Initialize module
#-----------------------------------------------------------------------
def init(params):
    ''' Initialize model and state'''

    model, err, msg = _init_model(params)
    if err:
        return None, err, msg

    return _init_state(model, params)


#-----------------------------------------------------------------------
# Validate state
#-----------------------------------------------------------------------
def _validate_state(state, sender, recipient, subject, messages, attachments):
    err = 0
    msgs = []

    # Sender
    if not sender:
        msgs.append("Email sender must be provided")
    else:
        state.sender = sender

    # Recipient
    if not recipient:
        msgs.append("Email recipient must be provided")
    else:
        state.recipient = recipient

    # Subject
    if not subject:
        msgs.append("Email subject must be provided")
    else:
        state.subject = subject

    # Messages
    if not messages:
        msgs.append("Email messages must be provided")
    elif not messages.get('text/html', None) and not messages.get('text/plain', None):
        msgs.append("Email messages 'text/html' and/or 'text.plain' must be provided")
    else:
        state.messages = messages

    # (Attachements are optional)

    if msgs:
        err = 1
        msgs.insert(0, "Email contains errors:")

    return err, ', '.join(msgs)


#-----------------------------------------------------------------------
# Execute
#-----------------------------------------------------------------------
def execute(state, sender, recipient, subject, messages, attachments):
    """
    Executes
    """

    # Set state
    err, msg = _validate_state(state, sender, recipient, subject, messages, attachments)
    if err:
        return err, msg

    _D.OBJECT(__name__, "Email Model", state.model)
    _D.OBJECT(__name__, "Email State", state)

    # Send email
    try:
        err, msg = _execute(state)

    except Exception as e:
        _D.EXCEPTION(__name__, "Exception executing emailer")
        err = 1
        msg = "Emailer executed with error: {}".format(e)

    finally:
        return err, msg


#-----------------------------------------------------------------------
# Cleanup
#-----------------------------------------------------------------------
def cleanup(state):
    """
    Cleans after execution
    """
    pass


#-----------------------------------------------------------------------
# Cleanup
#-----------------------------------------------------------------------
def send_report(emailconfrstate, subject, message_filepath, attachments):
    with open(message_filepath) as f:
        message = {'text/html': f.read()}

    state, err, msg = init(
            emailconfrstate,
            emailconfrstate.params.get('sender', None),
            emailconfrstate.params.get('recipient', None),
            subject,
            message,
            attachments
            )
    if err:
        return None, err, msg

    _, err, msg = execute(state)
    if err:
        return None, err, msg

    cleanup(state)
    return state, 0, None
