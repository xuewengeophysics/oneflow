"""
Copyright 2020 The OneFlow Authors. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import traceback
import oneflow.core.job.job_conf_pb2 as job_conf_pb
import oneflow.python.framework.scope_symbol as scope_symbol
import oneflow.python.eager.vm_util as vm_util
from contextlib import contextmanager
from oneflow.python.oneflow_export import oneflow_export, oneflow_deprecate


@oneflow_export("current_scope")
def api_current_scope():
    r""" Return current scope
    """
    return GetCurrentScope()


@oneflow_export("scope.current_scope")
@oneflow_deprecate()
def deprecated_current_scope(*args, **kwargs):
    print(
        "WARNING:",
        "oneflow.scope.current_scope",
        "will be removed in the future, use {} instead.".format(
            "oneflow.current_scope"
        ),
    )
    print(traceback.format_stack()[-2])

    return api_current_scope(*args, **kwargs)


def MakeScope(build_func):
    scope = None
    old_scope = GetCurrentScope()
    assert old_scope is not None

    def BuildScope(builder):
        nonlocal scope
        scope = build_func(old_scope, builder)
        assert scope is not None

    vm_util.LogicalRun(BuildScope)
    return scope


def MakeInitialScope(job_conf, device_tag, machine_device_ids, is_mirrored):
    scope = None

    def BuildInitialScope(builder):
        nonlocal scope
        scope = scope_symbol.BuildInitialScope(
            builder, job_conf, device_tag, machine_device_ids, is_mirrored
        )

    vm_util.LogicalRun(BuildInitialScope)
    return scope


def InitScopeStack():
    job_conf = job_conf_pb.JobConfigProto()
    job_conf.predict_conf.SetInParent()
    job_conf.job_name = ""
    scope = MakeInitialScope(job_conf, "cpu", ["0:0"], is_mirrored=False)
    global scope_stack_
    scope_stack_ = [scope]


@contextmanager
def ScopeContext(scope):
    old_scope = GetCurrentScope()
    scope_stack_.append(scope)
    try:
        yield
    finally:
        assert GetCurrentScope() is scope
        scope_stack_.pop()
        assert GetCurrentScope() is old_scope


def GetCurrentScope():
    assert len(scope_stack_) > 0
    return scope_stack_[-1]


scope_stack_ = []
