#ifndef MYPYC_NATIVE_H
#define MYPYC_NATIVE_H
#include <Python.h>
#include <CPy.h>
#ifndef MYPYC_DECLARED_tuple_T3OOO
#define MYPYC_DECLARED_tuple_T3OOO
typedef struct tuple_T3OOO {
    PyObject *f0;
    PyObject *f1;
    PyObject *f2;
} tuple_T3OOO;
#endif

#ifndef MYPYC_DECLARED_tuple_T2II
#define MYPYC_DECLARED_tuple_T2II
typedef struct tuple_T2II {
    CPyTagged f0;
    CPyTagged f1;
} tuple_T2II;
#endif

#ifndef MYPYC_DECLARED_tuple_T3CIO
#define MYPYC_DECLARED_tuple_T3CIO
typedef struct tuple_T3CIO {
    char f0;
    CPyTagged f1;
    PyObject *f2;
} tuple_T3CIO;
#endif

#ifndef MYPYC_DECLARED_tuple_T2OO
#define MYPYC_DECLARED_tuple_T2OO
typedef struct tuple_T2OO {
    PyObject *f0;
    PyObject *f1;
} tuple_T2OO;
#endif

#ifndef MYPYC_DECLARED_tuple_T1O
#define MYPYC_DECLARED_tuple_T1O
typedef struct tuple_T1O {
    PyObject *f0;
} tuple_T1O;
#endif

#ifndef MYPYC_DECLARED_tuple_T0
#define MYPYC_DECLARED_tuple_T0
typedef struct tuple_T0 {
    int empty_struct_error_flag;
} tuple_T0;
#endif

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *_task;
    PyObject *_later_call;
    CPyTagged _waiters;
} async_lru____CacheItemObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
    PyObject *___module__;
    PyObject *___name__;
    PyObject *___qualname__;
    PyObject *___doc__;
    PyObject *___annotations__;
    PyObject *___wrapped__;
    PyObject *___maxsize;
    char ___typed;
    PyObject *___ttl;
    PyObject *___cache;
    char ___closed;
    CPyTagged ___hits;
    CPyTagged ___misses;
} async_lru____LRUCacheWrapperObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
    PyObject *___module__;
    PyObject *___name__;
    PyObject *___qualname__;
    PyObject *___doc__;
    PyObject *___annotations__;
    PyObject *___wrapped__;
    PyObject *___instance;
    PyObject *___wrapper;
} async_lru____LRUCacheWrapperInstanceMethodObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *___mypyc_generator_attribute__self;
    char ___mypyc_generator_attribute__wait;
    int32_t ___mypyc_next_label__;
    PyObject *___mypyc_generator_attribute__tasks;
    PyObject *___mypyc_temp__0;
    int64_t ___mypyc_temp__1;
    PyObject *___mypyc_generator_attribute__task;
    PyObject *___mypyc_temp__2;
    tuple_T3OOO ___mypyc_temp__3;
} async_lru___cache_close__LRUCacheWrapper_genObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *___mypyc_generator_attribute__self;
    PyObject *___mypyc_generator_attribute__cache_item;
    PyObject *___mypyc_generator_attribute__key;
    int32_t ___mypyc_next_label__;
    PyObject *___mypyc_generator_attribute__task;
    PyObject *___mypyc_temp__4;
    tuple_T3OOO ___mypyc_temp__5;
    PyObject *___mypyc_temp__6;
    tuple_T3OOO ___mypyc_temp__7;
} async_lru____shield_and_handle_cancelled_error__LRUCacheWrapper_genObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *___mypyc_generator_attribute__self;
    PyObject *___mypyc_generator_attribute__fn_args;
    PyObject *___mypyc_generator_attribute__fn_kwargs;
    int32_t ___mypyc_next_label__;
    PyObject *___mypyc_generator_attribute__task;
    PyObject *___mypyc_generator_attribute__loop;
    PyObject *___mypyc_generator_attribute__key;
    PyObject *___mypyc_generator_attribute__cache;
    PyObject *___mypyc_generator_attribute__cache_item;
    PyObject *___mypyc_temp__8;
    tuple_T3OOO ___mypyc_temp__9;
    PyObject *___mypyc_generator_attribute__coro;
    PyObject *___mypyc_generator_attribute__maxsize;
    PyObject *___mypyc_generator_attribute__dropped_key;
    PyObject *___mypyc_generator_attribute__dropped_cache_item;
    PyObject *___mypyc_temp__10;
    tuple_T3OOO ___mypyc_temp__11;
} async_lru_____call___3__LRUCacheWrapper_genObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *___mypyc_generator_attribute__self;
    char ___mypyc_generator_attribute__cancel;
    char ___mypyc_generator_attribute__return_exceptions;
    int32_t ___mypyc_next_label__;
    PyObject *___mypyc_temp__12;
    tuple_T3OOO ___mypyc_temp__13;
} async_lru___cache_close__LRUCacheWrapperInstanceMethod_genObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *___mypyc_generator_attribute__self;
    PyObject *___mypyc_generator_attribute__fn_args;
    PyObject *___mypyc_generator_attribute__fn_kwargs;
    int32_t ___mypyc_next_label__;
    PyObject *___mypyc_temp__14;
    tuple_T3OOO ___mypyc_temp__15;
} async_lru_____call___3__LRUCacheWrapperInstanceMethod_genObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *___mypyc_self__;
    PyObject *_maxsize;
    char _typed;
    PyObject *_ttl;
    PyObject *_wrapper;
} async_lru____make_wrapper_envObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
    PyObject *___mypyc_env__;
} async_lru___wrapper__make_wrapper_objObject;

#endif
