from scalr import app
from werkzeug.debug import DebuggedApplication

application = DebuggedApplication(app, True)
