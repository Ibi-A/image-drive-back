#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from '@aws-cdk/core';
import { ImagesBackStack } from '../lib/images-back-stack';

const app = new cdk.App();
new ImagesBackStack(app, 'ImagesBackStack');
