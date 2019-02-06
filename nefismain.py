"""
Main module for nefis files.

Python 2.7 only.
"""

from netCDF4 import Dataset
import numpy as np
import struct
import nefis
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
    nt : list

        List of starting and ending index. 1-indexed.

    """
    # TODO add in a funtion that automatically
    # determines which group a variable is in

    # Retrieve number of available timesteps
    error, ntimes = nefis.inqmxi(fp, grp_name)
    neferrcheck(error)

    elm_dimensions = blankdims()

    (error, elm_type, elm_single_byte,
     elm_quantity, elm_unit,
     elm_description, elm_count) = nefis.inqelm(fp, elm_name, elm_dimensions)

    # Get rid of invalid dims.
    elm_dimensions = elm_dimensions[elm_dimensions > 0]

    # print_elmstuff(elm_name, elm_type, elm_single_byte, elm_quantity,
    #                elm_unit, elm_dimensions, elm_count)

    usr_index = np.zeros(15, dtype=np.int32).reshape(5, 3)

    usr_index[0, 0] = 1  # first timestep
    usr_index[0, 1] = ntimes  # last time step
    usr_index[0, 2] = 1  # increment
    np.ascontiguousarray(usr_index, dtype=np.int32)

    if ntimes > 1:
        elm_dimensions = np.array(list(elm_dimensions) + [ntimes])
    numnums = np.prod(elm_dimensions)

    numbytes = numnums * elm_single_byte

    usr_order = userorder()

    error, buffer_res = nefis.getelt(fp, grp_name, elm_name,
                                     usr_index, usr_order, numbytes)

    neferrcheck(error)

    if 'INT' in elm_type:
        fmt = "%di" % (numnums)
        # pdb.set_trace()
    else:
        fmt = "%df" % (numnums)  # format string for float return.

    # Not sure why I need to reverse the dims
    # Reverse dimensions (C vs Fortran ??)
    dims2 = elm_dimensions[::-1]

    # Unpack data into numpy array.
    numbers = np.asarray(struct.unpack(fmt, buffer_res)).reshape(dims2)
    # numbers = np.squeeze(numbers)

    # print(np.shape(numbers))
    return numbers


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
    t1, _ = getgroups(fd)
    d1 = {}

    for i in t1:
        elems = getelems(fd, i)
        infos = {}
        for j in elems:

            elmdict = getelem(fd, j)
            if 'CHAR' in elmdict['dtype']:
                pass
            else:
                elmdict['data'] = get_data(fd, j, i)
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


def trim2nc(fname):
    """Convert trim data to netCDF4 file."""
    fd = openfile(fname)
    d1 = getalldata(fd)
    gn, nti = getgroups(fd)
    closefile(fd)

    print('Note: You must specify the coordinate system later.')
    rootgrp = Dataset(fname[:-4] + '.nc', 'w', format='NETCDF4')
    # Don't use groups right now.

    # coord = d1['map-const']['COORDINATES']['data']
    idate = d1['map-const']['ITDATE']['data']
    tpoints = d1['map-info-series']['ITMAPC']['data']

    xz = d1['map-const']['XZ']
    # yz = d1['map-const']['YZ']
    # d1['map-const']['XCOR']
    # d1['map-const']['YCOR']

    ms = rootgrp.createDimension('m', xz['dimensions'][0])  # noqa
    ns = rootgrp.createDimension('n', xz['dimensions'][1])  # noqa
    ts = rootgrp.createDimension('t', nti['map-series'])  # noqa

    times = rootgrp.createVariable('tsecs', 'i4', ('t',))
    times[:] = tpoints
    times.description = 'Seconds from start of simulation'

    rootgrp.itdate = str(idate[0]) + ' ' + str(idate[1])

    # Only do the data blocks that have dimensions ms/ns within map-const
    # and map-series. So only 2D output data.
    varc, vars = [], []
    for keys, vals in d1['map-const'].iteritems():
        if (all(vals['dimensions'][:2] == xz['dimensions']) and
                len(vals['dimensions']) == 2):
            if 'data' in vals:
                if 'REAL' in vals['dtype']:
                    dty = 'f4'
                elif 'INT' in vals['dtype']:
                    dty = 'i4'
                varc.append(rootgrp.createVariable(vals['name'], dty,
                                                   ('n', 'm',)))
                varc[-1].description = vals['description']
                varc[-1].unit = vals['unit']
                varc[-1][:] = vals['data']
    for keys, vals in d1['map-series'].iteritems():
        # print(keys)
        # if keys == 'VICWW':
        # print(vals['dimensions'])
        # pdb.set_trace()
        if (all(vals['dimensions'][:2] == xz['dimensions'])
                and len(vals['dimensions']) == 2):
            if 'data' in vals:
                if 'REAL' in vals['dtype']:
                    dty = 'f4'
                elif 'INT' in vals['dtype']:
                    dty = 'i4'
                vars.append(rootgrp.createVariable(vals['name'], dty,
                                                   ('t', 'n', 'm',)))
                vars[-1].description = vals['description']
                vars[-1].unit = vals['unit']
                vars[-1][:] = vals['data']
    rootgrp.close()


if __name__ == '__main__':
    funname = sys.argv[1]
    fname = sys.argv[2]
    if 'trim2nc' in funname:
        trim2nc(fname)
