# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from aria.parser import validation
from aria.storage.modeling import utils
from aria.utils.collections import deepcopy_with_locators
from aria.storage.modeling import model


@model.ServiceTemplate.instantiates(instance_cls=model.ServiceInstance)
def instantiate_service(self, instance_cls, context, container):
    service_instance = instance_cls()
    context.modeling.instance = service_instance

    service_instance.description = deepcopy_with_locators(self.description)

    if self.metadata is not None:
        service_instance.metadata = self.metadata.instantiate(context, container)

    for node_template in self.node_templates.itervalues():
        for _ in range(node_template.default_instances):
            node = node_template.instantiate(context, container)
            service_instance.nodes[node.id] = node

    utils.instantiate_dict(context, self, service_instance.groups, self.group_templates)
    utils.instantiate_dict(context, self, service_instance.policies, self.policy_templates)
    utils.instantiate_dict(context, self, service_instance.operations, self.operation_templates)

    if self.substitution_template is not None:
        service_instance.substitution = self.substitution_template.instantiate(context,
                                                                               container)

    utils.instantiate_dict(context, self, service_instance.inputs, self.inputs)
    utils.instantiate_dict(context, self, service_instance.outputs, self.outputs)

    for name, the_input in context.modeling.inputs.iteritems():
        if name not in service_instance.inputs:
            context.validation.report('input "%s" is not supported' % name)
        else:
            service_instance.inputs[name].value = the_input

    return service_instance


@model.ArtifactTemplate.instantiates(instance_cls=model.Artifact)
def instantiate_artifact(self, instance_cls, context, container):
    artifact = instance_cls(self.name, self.type_name, self.source_path)
    artifact.description = deepcopy_with_locators(self.description)
    artifact.target_path = self.target_path
    artifact.repository_url = self.repository_url
    artifact.repository_credential = self.repository_credential
    utils.instantiate_dict(context, container, artifact.properties, self.properties)
    return artifact


@model.CapabilityTemplate.instantiates(instance_cls=model.Capability)
def instantiate_capability(self, instance_cls, context, container):
    capability = instance_cls(self.name, self.type_name)
    capability.min_occurrences = self.min_occurrences
    capability.max_occurrences = self.max_occurrences
    utils.instantiate_dict(context, container, capability.properties, self.properties)
    return capability


@model.InterfaceTemplate.instantiates(instance_cls=model.Interface)
def instantiate_interface(self, instance_cls, context, container):
    interface = instance_cls(self.name, self.type_name)
    interface.description = deepcopy_with_locators(self.description)
    utils.instantiate_dict(context, container, interface.inputs, self.inputs)
    utils.instantiate_dict(context, container, interface.operations, self.operation_templates)
    return interface


@model.OperationTemplate.instantiates(instance_cls=model.Operation)
def instantiate_operation(self, instance_cls, context, container):
    operation = instance_cls(self.name)
    operation.description = deepcopy_with_locators(self.description)
    operation.implementation = self.implementation
    operation.dependencies = self.dependencies
    operation.executor = self.executor
    operation.max_retries = self.max_retries
    operation.retry_interval = self.retry_interval
    utils.instantiate_dict(context, container, operation.inputs, self.inputs)
    return operation


@model.PolicyTemplate.instantiates(instance_cls=model.Policy)
def instantiate_policy(self, instance_cls, context, **kwargs):
    policy = instance_cls(self.name, self.type_name)
    utils.instantiate_dict(context, self, policy.properties, self.properties)
    for node_template_name in self.target_node_template_names:
        policy.target_node_ids.extend(
            context.modeling.instance.get_node_ids(node_template_name))
    for group_template_name in self.target_group_template_names:
        policy.target_group_ids.extend(
            context.modeling.instance.get_group_ids(group_template_name))
    return policy


@model.GroupPolicyTemplate.instantiates(instance_cls=model.GroupPolicy)
def instantiate_group_policy(self, instance_cls, context, container):
    group_policy = instance_cls(self.name, self.type_name)
    group_policy.description = deepcopy_with_locators(self.description)
    utils.instantiate_dict(context, container, group_policy.properties, self.properties)
    utils.instantiate_dict(context, container, group_policy.triggers, self.triggers)
    return group_policy


@model.GroupPolicyTriggerTemplate.instantiates(instance_cls=model.GroupPolicyTrigger)
def instantiate_group_policy_trigger(self, instance_cls, context, container):
    group_policy_trigger = instance_cls(self.name, self.implementation)
    group_policy_trigger.description = deepcopy_with_locators(self.description)
    utils.instantiate_dict(context, container, group_policy_trigger.properties, self.properties)
    return group_policy_trigger


@model.MappingTemplate.instantiates(instance_cls=model.Mapping)
def instantiate_mapping(self, instance_cls, context, container):
    nodes = context.modeling.instance.find_nodes(self.node_template_name)
    if len(nodes) == 0:
        context.validation.report(
            'mapping "%s" refer to node template "%s" but there are no '
            'node instances' % (self.mapped_name,
                                self.node_template_name),
            level=validation.Issue.BETWEEN_INSTANCES)
        return None
    return instance_cls(self.mapped_name, nodes[0].id, self.name)


@model.SubstitutionTemplate.instantiates(instance_cls=model.Substitution)
def instantiate_substitution(self, instance_cls, context, container):
    substitution = instance_cls(self.node_type_name)
    utils.instantiate_dict(context, container, substitution.capabilities,
                           self.capability_templates)
    utils.instantiate_dict(context, container, substitution.requirements,
                           self.requirement_templates)
    return substitution


@model.NodeTemplate.instantiates(instance_cls=model.Node)
def instantiate_node(self, instance_cls, context, **kwargs):
    node = instance_cls(context, self.type_name, self.name)
    utils.instantiate_dict(context, node, node.properties, self.properties)
    utils.instantiate_dict(context, node, node.interfaces, self.interface_templates)
    utils.instantiate_dict(context, node, node.artifacts, self.artifact_templates)
    utils.instantiate_dict(context, node, node.capabilities, self.capability_templates)
    return node


@model.GroupTemplate.instantiates(instance_cls=model.Group)
def instantiate_node(self, instance_cls, context, **kwargs):
    group = instance_cls(context, self.type_name, self.name)
    utils.instantiate_dict(context, self, group.properties, self.properties)
    utils.instantiate_dict(context, self, group.interfaces, self.interface_templates)
    utils.instantiate_dict(context, self, group.policies, self.policy_templates)
    for member_node_template_name in self.member_node_template_names:
        group.member_node_ids += \
            context.modeling.instance.get_node_ids(member_node_template_name)
    for member_group_template_name in self.member_group_template_names:
        group.member_group_ids += \
            context.modeling.instance.get_group_ids(member_group_template_name)
    return group
