#ifndef BILLIARD_WRITER_H
#define BILLIARD_WRITER_H

#include "Python.h"
#include "structmember.h"
#include "pythread.h"

#if PY_VERSION_HEX >= 0x03000000 /* 3.0 and up */
#  define PyString_FROM_FORMAT PyUnicode_FromFormat
#  define PyInt_FromLong PyLong_FromLong
#  define PyInt_FromSsize_t PyLong_FromSsize_t
#  define PyString_INTERN_FROM_STRING PyString_FromString
#else                            /* 2.x */
#  define PyString_FROM_FORMAT PyString_FromFormat
#  define PyString_INTERN_FROM_STRING PyString_InternFromString
#endif

typedef struct {
    PyObject_HEAD
    PyObject *proc;
    PyObject *fd;
    PyObject *job;
    PyObject *header;
    PyObject *body;
    Py_ssize_t body_size;
    Py_ssize_t offset;
    PyObject *weakreflist;
} Billiard_MsgWriter;

static PyObject *
Billiard_MsgWriterType_new(PyTypeObject *, PyObject *, PyObject *);

PyObject *
Billiard_MsgWriter_getiter(Billiard_MsgWriter *);

PyObject *
Billiard_MsgWriter_iternext(Billiard_MsgWriter *);

static PyObject *
Billiard_MsgWriterType_repr(Billiard_MsgWriter *);

static void
Billiard_MsgWriterType_dealloc(Billiard_MsgWriter *);

PyDoc_STRVAR(
    Billiard_MsgWriterType_doc,
    "Pool message writer object\n"
);

static PyMemberDef Billiard_MsgWriterType_members[] = {
    {"proc", T_OBJECT_EX,
        offsetof(Billiard_MsgWriter, proc), READONLY, NULL},
    {"fd", T_OBJECT_EX,
        offsetof(Billiard_MsgWriter, fd), READONLY, NULL},
    {"job", T_OBJECT_EX,
        offsetof(Billiard_MsgWriter, job), READONLY, NULL},
    {"header", T_OBJECT_EX,
        offsetof(Billiard_MsgWriter, header), READONLY, NULL},
    {"body", T_OBJECT_EX,
        offsetof(Billiard_MsgWriter, body), READONLY, NULL},
    {"body_size", T_PYSSIZET,
        offsetof(Billiard_MsgWriter, body), READONLY, NULL},
    {NULL, 0, 0, 0, NULL}
};

static PyMethodDef Billiard_MsgWriterType_methods[] = {
    {NULL}
};

PyTypeObject Billiard_MsgWriterType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    /* tp_name */           "_billiard.MsgWriter",
    /* tp_basicsize */      sizeof(Billiard_MsgWriter),
    /* tp_itemsize */       0,
    /* tp_dealloc */        (destructor)Billiard_MsgWriterType_dealloc,
    /* tp_print */          0,
    /* tp_getattr */        0,
    /* tp_setattr */        0,
    /* tp_compare */        0,
    /* tp_repr */           (reprfunc)Billiard_MsgWriterType_repr,
    /* tp_as_number */      0,
    /* tp_as_sequence */    0,
    /* tp_as_mapping */     0,
    /* tp_hash */           0,
    /* tp_call */           0,
    /* tp_str */            0,
    /* tp_getattro */       0,
    /* tp_setattro */       0,
    /* tp_as_buffer */      0,
    /* tp_flags */          Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE |
                            Py_TPFLAGS_HAVE_WEAKREFS,
    /* tp_doc */            Billiard_MsgWriterType_doc,
    /* tp_traverse */       0,
    /* tp_clear */          0,
    /* tp_richcompare */    0,
    /* tp_weaklistoffset */ offsetof(Billiard_MsgWriter, weakreflist),
    /* tp_iter */           (getiterfunc)Billiard_MsgWriter_getiter,
    /* tp_iternext */       (iternextfunc)Billiard_MsgWriter_iternext,
    /* tp_methods */        Billiard_MsgWriterType_methods,
    /* tp_members */        Billiard_MsgWriterType_members,
    /* tp_getset */         0,
    /* tp_base */           0,
    /* tp_dict */           0,
    /* tp_descr_get */      0,
    /* tp_descr_set */      0,
    /* tp_dictoffset */     0,
    /* tp_init */           0,
    /* tp_alloc */          0,
    /* tp_new */            (newfunc)Billiard_MsgWriterType_new,
    /* tp_free */           0,
    /* tp_is_gc */          0,
    /* tp_bases */          0,
    /* tp_mro */            0,
    /* tp_cache */          0,
    /* tp_subclasses */     0,
    /* tp_weaklist */       0,
    /* tp_del */            0,
    /* tp_version_tag */    0x010000000,
};

#endif  // BILLIARD_WRITER_H
