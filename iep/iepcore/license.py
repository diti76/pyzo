# -*- coding: utf-8 -*-
# Copyright (C) 2013, the IEP development team
#
# IEP is distributed under the terms of the (new) BSD License.
# The full license can be found in 'license.txt'.

""" Code related to the license.
"""

import os
import sys
import datetime

import iep
from iep.codeeditor.qt import QtCore, QtGui


LICENSEKEY_FILE = os.path.join(iep.appDataDir, "licensekey.txt")

UNMANGLE_CODE ="""
eJytUsFu2zAMvecr2OQgGXOMJU23wViOPRTboYehwxAEgyrRiTBHEiQ5XVHs30vJjrMBW9HDdLFF
vvfIR3EGX7FtQVmDF/DNdnAQRuxQQbSgUFqFEPcIrZZoAkJnKL9rEZrOyKituZjMYA4ed8KrUMIX
wt5c3xL1iK11BzQRIorDRGEzknko6gnQmU6n8LlXnv/Ax1QzRK/NLlfXMlYnWP46j43+WcL3EsIK
1hCqhHa8qJzwUad2OJuz4jcwoe5FwHerqjdz/xgx8D5XoUkhzkSQWrOiGDCcdbGZfxh0dAPGRhg4
IIyi4kP/6XihaS53ou3w2nvrOftEThJFmzyK0+ga6w8iVn/KDp2ESAbCg457zjQ6mgX7zyVgvYZB
+rhgL2nfmKNotYIj+kATBdu8UCNc/n3CYfW66YYl8RnL/9J2tC1reJ9vVAdkMhguz932kDcnTHZJ
DOsVlwXtYc6PqYe9pk3VH9+eBXoGCSyvrsYgNUERufdcD10t/uFq+TpXiuhPv/o1TA9L143Ljlx2
tKiCa3XkrK5rVqSHYjVLGbcdvdNDlUAvkcKbpDJyWLkoejGKZlaqsT2bVBsib6ko0ft+NiytVAoF
gBkIpZJ+znmMnTegngGt0S9m
"""


import types, base64, zlib
def parse_license(key):
    """ Unmangle the license key and return a dict with license info.
    The dict at least has these fields: 
    name, company, email, expires, product, reference.
    
    The actual code of this function is obfuscated. We realize that
    anyone with a bit of free time can find out the license parsing.
    The obfuscating is to make this a bit harder and to avoid having
    the code verbatim in the repository.
    
    You are free to reverse-engineer our license key format and then
    produce your own license. However, who would you be fooling?
    """
    # Define function
    codeb = zlib.decompress(base64.decodebytes(UNMANGLE_CODE.encode('ascii')))
    exec(codeb.decode('utf-8'), globals())
    # Call it
    return unmangle(key)
    



def get_keys():
    """ Get a list of all license keys. 
    """
    
    # Get text of license file
    if os.path.isfile(LICENSEKEY_FILE):
        text = open(LICENSEKEY_FILE, 'rt').read()
    else:
        text = ''
    
    # Remove comments
    lines = []
    for line in text.splitlines():
        if line.startswith('#'):
            line = ''
        lines.append(line.rstrip())
    
    # Split in licenses
    licenses = ('\n'.join(lines)).split('\n\n')
    licenses = [key.strip() for key in licenses]    
    licenses = [key for key in licenses if key]
    
    # Remove duplicates (avoid set() to maintain order)
    licenses, licenses2 = [], licenses
    for key in licenses2:
        if key not in licenses:
            licenses.append(key)
    
    return licenses


def is_invalid(info):
    """ Get whether a license is invalid. Returns a string with the reason.
    """
    # IEP license?
    if not ('IEP' in info['product'].upper() or 
            'PYZO' in info['product'].upper() ):
        return 'This is not an IEP license.'
    # Expired
    today = datetime.datetime.now().strftime('%Y%m%d')
    if today > info['expires']:
        return 'The license has expired'


def get_license_info():
    """ Get the license info of the most recent valid license.
    Returns a dict which at least has these fields: 
    name, company, email, expires, product, reference.
    Returns None if there is no valid license.
    """
    
    # Get all keys
    licenses = get_keys()
    
    # Get valid licenses
    valid_licenses = []
    for key in licenses:
        info = parse_license(key)
        if not is_invalid(info):
            valid_licenses.append(info)
    
    # Done
    if valid_licenses:
        return valid_licenses[-1]
    else:
        return None



def add_license(key):
    """ Add a license key to IEP.
    """
    
    # Normalize and check license
    key = key.strip().replace('\n', '').replace('\r', '')
    info = parse_license(key)
    invalid = is_invalid(info)
    if invalid:
        raise ValueError('Given license is not valid: %s' % invalid)
    
    # Get licenses and add our key
    licenses = get_keys()
    licenses.append(key)
    
    # Remove duplicates (avoid set() to maintain order)
    licenses, licenses2 = [], licenses
    for key in licenses2:
        if key not in licenses:
            licenses.append(key)
    
    # Write back
    lines = ['# List of license keys for IEP', '']
    for key in licenses:
        info = parse_license(key)
        comment = '# Licensed to {name} expires {expires}'.format(**info)
        lines.append(comment)
        lines.append(key)
    with open(LICENSEKEY_FILE, 'wt') as f:
        f.write('\n'.join(lines))



class LicenseManager(QtGui.QDialog):
    """ Dialog to view current licenses and to add license keys.
    """
    
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle(iep.translate("menu dialog", "Manage IEP license keys"))
        self.resize(500,500)
        
        # Create button to add license key
        self._addbut = QtGui.QPushButton(
            iep.translate("menu dialog", "Add license key") )
        self._addbut.clicked.connect(self.addLicenseKey)
        
        # Create label to show license info
        self._label = QtGui.QTextEdit(self)
        self._label.setLineWrapMode(self._label.WidgetWidth)
        self._label.setReadOnly(True)
        
        # Layout
        layout = QtGui.QVBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(self._addbut)
        layout.addWidget(self._label)
        
        # Init
        self.showLicenses()
    
    
    def addLicenseKey(self):
        """ Show dialog to insert new key.
        """
        # Ask for key
        title = iep.translate("menu dialog", "Add license key")
        label = ''
        s = QtGui.QInputDialog.getText(self, title, label, 
                QtGui.QLineEdit.Normal, '')
        if isinstance(s, tuple):
            s = s[0] if s[1] else ''
        
        # Add it
        if s:
            try:
                add_license(s)
            except Exception as err:
                label = 'Could not add label:\n%s' % str(err)
                QtGui.QMessageBox.warning(self, title, label)
        
        # Update
        self.showLicenses()
        iep.license = get_license_info()
    
    
    def showLicenses(self):
        """ Show all licenses.
        """
        # Get active license
        activeLicense = get_license_info()
        
        # Get all keys
        licenses = get_keys()
        
        lines = ['Licenses from "%s":' % LICENSEKEY_FILE]
        for key in licenses:
            # Get info 
            info = parse_license(key)
            activeText = ''
            if activeLicense and activeLicense['key'] == info['key']:
                activeText = ' (active)'
            e = datetime.datetime.strptime(info['expires'], '%Y%m%d')
            expires = e.strftime('%d-%m-%Y')
            # Create summary
            lines.append('<p>')
            lines.append('<b>%s</b>%s<br />' % (info['product'], activeText))
            lines.append('Name: %s<br />' % info['name'])
            lines.append('Email: %s<br />' % info['email'])
            lines.append('Company: %s<br />' % info['company'])
            lines.append('Expires: %s<br />' % expires)
            lines.append('key: <tiny><sub>%s</sub></tiny><br />' % key)
            lines.append('</p>')
        
        # No licenses?
        if not licenses:
            lines.append('No licenses keys found.')
        
        # Set label text
        self._label.setHtml('\n'.join(lines))


if __name__ == '__main__':
    w = LicenseManager(None)
    w.show()

    