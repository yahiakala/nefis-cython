"""
Main module for nefis files.

Python 2.7 only.
"""

from netCDF4 import Dataset
from lib import nefis
import numpy as np
import struct
import pdb  # noqa
import sys


def openfile(datfile):
    """Open file and return identifier."""
    dat_file = datfile
    def_file = datfile[:-4] + '.def'
    coding = ' '
    ac_type = 'r'

    error, fp = nefis.crenef(dat_file, def_file, coding, ac_type)
    neferrcheck(error)
    return fp


def closefile(fp):
    """Close nefis file."""
    error = nefis.clsnef(fp)
    neferrcheck(error)


def blankdims():
    """Return a contiguous array (c order) of blank dimensions."""
    bdim = np.arange(5)
    bdim[0] = -1
    bdim[1] = -1
    bdim[2] = -1
    bdim[3] = -1
    bdim[4] = -1
    np.ascontiguousarray(bdim, dtype=np.int32)
    return bdim


def userorder():
    """Return user order arg."""
    usr_order = np.arange(5)
    usr_order[0] = 1
    usr_order[1] = 2
    usr_order[2] = 3
    usr_order[3] = 4
    usr_order[4] = 5
    np.ascontiguousarray(usr_order, dtype=np.int32)
    return usr_order


def print_elmstuff(elm_name, elm_type, elm_single_byte, elm_quantity,
                   elm_unit, elm_dimensions, elm_count):
    """Print off some element information."""
    print(elm_name, ' description: ', elm_name)
    print(elm_name, '    type    : ', elm_type)
    print(elm_name, ' byte size  : ', elm_single_byte)
    print(elm_name, ' quantity   : ', elm_quantity)
    print(elm_name, ' units      : ', elm_unit)
    print(elm_name, ' dimensions : ', elm_dimensions)
    print(elm_name, '    size    : ', elm_count)


def neferrcheck(errin):
    """Print out error message."""
    if not errin == 0:
        print("=========")
        error, err_string = nefis.neferr()
        print('    NEFIS error string       : %s' % err_string)
        print("=========")


def get_data(fp, elm_name, grp_name):
    """
    Get dynamic variable output.

    Parameters
    ----------
    fd : int

        File identifier.

    elm_name : string

        Name of element.

    grp_name : string

        Name of group.

    Returns
    -------
    data : np.array

    """
    # Retrieve number of available timesteps
    error, ntimes = nefis.inqmxi(fp, grp_name)
    neferrcheck(error)

    elm_dimensions = blankdims()

    (error, elm_type, elm_single_byte,
     elm_quantity, elm_unit,
     elm_description, elm_count) = nefis.inqelm(fp, elm_name, elm_dimensions)

    # Get rid of invalid dims.
    elm_dimensions = elm_dimensions[elm_dimensions > 0]

    usr_order = userorder()
    usr_index = np.zeros(15, dtype=np.int32).reshape(5, 3)

    usr_index[0, 0] = 1  # first timestep
    usr_index[0, 1] = ntimes  # last time step
    usr_index[0, 2] = 1  # increment
    np.ascontiguousarray(usr_index, dtype=np.int32)

    if ntimes > 1:
        dims1 = np.array(list(elm_dimensions) + [ntimes])
    else:
        dims1 = elm_dimensions

    if np.prod(dims1) >= sys.maxint or np.prod(dims1) < 0:
        print('Data too large: skipping ' + elm_name)
        return np.zeros(dims1[::-1])

    dims2 = dims1[::-1]
    numnums = np.prod(dims1)
    elm_tbytes = numnums * elm_single_byte

    if 'INT' in elm_type:
        fmt = "%di" % (numnums)
        # pdb.set_trace()
    elif 'REAL' in elm_type:
        if elm_single_byte == 4:
            fmt = "%df" % (numnums)
        else:
            fmt = "%dd" % (numnums)  # format string for float/double return.
    else:
        fmt = "%ds" % (numnums)  # string

    if 'CHAR' in elm_type:
        error, buffer_res = nefis.getels(fp, grp_name, elm_name,
                                         usr_index, usr_order, elm_tbytes)
        dats = [buffer_res[i:i + elm_single_byte].strip()
                for i in range(0, len(buffer_res), elm_single_byte)]
        dats = np.array(dats)
    else:
        error, buffer_res = nefis.getelt(fp, grp_name, elm_name,
                                         usr_index, usr_order, elm_tbytes)
        dats = np.asarray(struct.unpack(fmt, buffer_res)).reshape(dims2)

    # if elm_name == 'SIMDAT':
    #     print_elmstuff(elm_name, elm_type, elm_single_byte, elm_quantity,
    #                    elm_unit, elm_dimensions, elm_count)
    #     pdb.set_trace()

    return dats


def getelem(fd, elm_name):
    """Get element data."""
    elm_dimensions = blankdims()
    (error, elm_type, elm_single_byte,
     elm_quantity, elm_unit,
     elm_description, elm_count) = nefis.inqelm(fd, elm_name, elm_dimensions)

    # Get rid of invalid dims.
    elm_dimensions = elm_dimensions[elm_dimensions > 0]

    return {'name': elm_name.strip(),
            'dtype': elm_type.strip(),
            'nbytes': elm_single_byte,
            'quantity': elm_quantity.strip(),
            'unit': elm_unit.strip(),
            'description': elm_description.strip(),
            'ndim': elm_count, 'dimensions': elm_dimensions,
            'tbytes': elm_single_byte * np.cumprod(elm_dimensions)[-1]}


def getelems(fd, grp_name):
    """Get elements in group."""
    status, el_names_count, c_elm_names = nefis.inqcel(fd, grp_name, 100)
    elmlist = [c_elm_names[i:i + 17].strip()
               for i in range(0, len(c_elm_names), 17)]
    return elmlist


def getalldata(fd):
    """Get all data in NEFIS file."""
    t1, nt = getgroups(fd)
    d1 = {}

    for i in t1:
        elems = getelems(fd, i)
        infos = {}
        for j in elems:
            elmdict = getelem(fd, j)
            elmdict['grpdim'] = nt[i]
            print('Getting ' + j + ' from ' + i)
            elmdict['data'] = get_data(fd, j, i)
            print('Got ' + j + ' from ' + i)
            infos[j] = elmdict
        d1[i] = infos
    return d1


def getgroups(fd):
    """Get list of data groups."""
    ee, n1, n2 = nefis.inqfst(fd)
    t1 = []
    t1.append(n1.strip())
    # t2.append(n2)

    for i in range(10):
        ee, c1, c2 = nefis.inqnxt(fd)
        if ee != 0:
            break
        else:
            t1.append(c1.strip())
            # t2.append(c2)

    nti = {}
    for grp_name in t1:
        error, ntimes = nefis.inqmxi(fd, grp_name)
        nti[grp_name] = ntimes
    return t1, nti


def nefis2nc(fname):
    """Convert trim data to netCDF4 file."""
    fd = openfile(fname)
    d1 = getalldata(fd)
    gn, nti = getgroups(fd)
    closefile(fd)

    # Get unique dimensions.
    dd = []
    for key1, val1 in d1.iteritems():
        for key2, val2 in val1.iteritems():
            dd += list(val2['dimensions']) + [val2['grpdim']]
    dda = np.unique(np.array(dd))
    dimnames = ['dim' + str(i + 1) for i in range(len(dda))]
    dda_dict = {}
    for i in range(len(dda)):
        dda_dict[dda[i]] = dimnames[i]

    print('Note: You must specify the coordinate system later.')
    rootgrp = Dataset(fname[:-4] + '.nc', 'w', format='NETCDF4')

    # Create dimensions from unique dimensions.
    dim_id = []
    for i in range(len(dda)):
        dim_id.append(rootgrp.createDimension(dimnames[i], dda[i]))

    # Create variables.
    var_id, grp_id = [], []
    for key1, val1 in d1.iteritems():
        grp_id.append(rootgrp.createGroup(key1))
        for key2, val2 in val1.iteritems():
            # Get shape of data and corresponding dims.
            newdims = list(np.shape(val2['data']))
            dimnami = [dda_dict[i] for i in newdims]
            if 'REAL' in val2['dtype']:
                dtype = 'f4'
            elif 'INT' in val2['dtype']:
                dtype = 'i4'
            else:
                dtype = np.unicode_
            print('Writing ' + val2['name'] + ' to netCDF')
            var_id.append(grp_id[-1].createVariable(
                val2['name'], dtype, tuple(dimnami)))
            var_id[-1].description = val2['description']
            var_id[-1].unit = val2['unit']
            var_id[-1][:] = val2['data']

    rootgrp.close()


if __name__ == '__main__':
    funname = sys.argv[1]
    fname = sys.argv[2]
    nefis2nc(fname)
