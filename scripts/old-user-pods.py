#!/usr/bin/env python3
"""
Delete all user pods older than a given duration.

We use the Kubernetes cluster autoscaler, which
removes nodes from the kubernetes cluster when they have
been 'empty' for more than 10 minutes However, we
have issues where some pods get 'stuck' and never actually
die, sometimes forever. This causes nodes to not be
killed automatically.

This script finds and (if --delete is given) kills all pods older than a given
number of hours

You need the `kubernetes` python library installed for this
to work.
"""
import argparse
from kubernetes import config, client
from datetime import datetime, timedelta, timezone

# Setup our parameters
argparser = argparse.ArgumentParser()
argparser.add_argument("hours", type=int, help="Pods older than this many hours will be killed")
argparser.add_argument("--delete", action="store_true", help="Confirm deleting the pods rather than just printing info")
argparser.add_argument("--namespace", default="prod", help="Namespace to perform actions in")

kube_context_help = ("Context pointing to the cluster to use. To list the "
                     "current activated context, run `kubectl config get-contexts`")
argparser.add_argument("--kube-context", default="gke_binder-prod_us-central1-a_prod-a", help=kube_context_help)
args = argparser.parse_args()

# Load and operate on current kubernetes config
config.load_kube_config(context=args.kube_context)

# Get list of pods with given label selector in the 'prod' namespace
core_api = client.CoreV1Api()

pods = core_api.list_namespaced_pod(args.namespace, label_selector="component=singleuser-server")
for pod in pods.items:
    # API results always use UTC timezone
    age = datetime.now(timezone.utc) - pod.status.start_time.replace(tzinfo=timezone.utc)
    print(age)
    if age > timedelta(hours=args.hours):
        if args.delete:
            core_api.delete_namespaced_pod(pod.metadata.name, args.namespace, client.V1DeleteOptions())
            print("Deleted {:.1f}h old pod {}".format(age.total_seconds() / 60 / 60, pod.metadata.name))
        else:
            print("Found {:.1f}h old pod {}".format(age.total_seconds() / 60 / 60, pod.metadata.name))
