#!/usr/bin/env python3

import aws_cdk as cdk

from mlops_cdk.mlops_cdk_stack import MlopsCdkStack


app = cdk.App()
MlopsCdkStack(app, "mlops-cdk")

app.synth()
