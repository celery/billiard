#include "writer.h"

/*
 * MsgWriter.__new__(fd, job)
 */
static PyObject *
Billiard_MsgWriterType_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    Billiard_MsgWriter *self = NULL;
    PyObject *proc = NULL;
    PyObject *fd = NULL;
    PyObject *job = NULL;

    static char *kwlist[] = {"proc", "fd", "job", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOO", kwlist,
                                     &proc, &fd, &job))
        return NULL;

    self = PyObject_New(Billiard_MsgWriter, type);
    if (self == NULL)
        goto error;

    PyObject *payload = PyObject_GetAttrString(job, "_payload");
    if (payload == NULL)
        goto error;
    PyObject *header = PyTuple_GET_ITEM(payload, 0);
    Py_INCREF(header);
    PyObject *body = PyTuple_GET_ITEM(payload, 1);
    Py_INCREF(body);
    PyObject *tmp = PyTuple_GET_ITEM(payload, 2);
    Py_ssize_t body_size = PyInt_AsSsize_t(tmp);

    self->weakreflist = NULL;
    self->proc = proc;
    self->fd = fd;
    self->job = job;
    self->header = header;
    self->body = body;
    self->body_size = body_size;
    self->offset = 0;

    return (PyObject*)self;
error:
    return NULL;
}


/*
 * MsgWriter.__iter__()
 *
 */
PyObject *
Billiard_MsgWriter_getiter(Billiard_MsgWriter *self)
{
    return (PyObject *)self;
}

/*
 * MsgWriter.__next__()
 *
 */
PyObject *
Billiard_MsgWriter_iternext(Billiard_MsgWriter *self)
{
    return NULL;
}

/*
 * MsgWriter.__repr__()
 */
static PyObject *
Billiard_MsgWriterType_repr(Billiard_MsgWriter *self)
{
    PyObject *repr = NULL;
    int fd = PyInt_AS_LONG(self->fd);
    if (self->fd == NULL) {
        repr = PyString_FROM_FORMAT("<MsgWriter: NO FD>");
        goto ok;
    }

    PyObject *fdr = PyObject_Repr(self->fd);
    if (fdr == NULL) goto error;

    if (self->job != NULL) {
        PyObject *jobr = PyObject_Repr(self->job);
        if (jobr == NULL) goto error;
        repr = PyString_FROM_FORMAT(
            "<MsgWriter: fd:%s job:%s>",
            PyString_AsString(fdr), PyString_AsString(jobr)
        );
        Py_XDECREF(jobr);
    } else {
        repr = PyString_FROM_FORMAT(
            "<MsgWriter: fd:%s INVALID JOB",
            PyString_AsString(fdr)
        );
    }
ok:
    return repr;
error:
    return NULL;
}

/*
 * MsgWriter.__del__()
 */
static void
Billiard_MsgWriterType_dealloc(Billiard_MsgWriter *self)
{
    if (self->weakreflist != NULL)
        PyObject_ClearWeakRefs((PyObject*)self);
    Py_XDECREF(self->proc);
    Py_XDECREF(self->fd);
    Py_XDECREF(self->job);
    Py_XDECREF(self->header);
    Py_XDECREF(self->body);
    self->ob_type->tp_free(self);
}
