#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from '@aws-cdk/core';
import { MemeagesBackStack } from '../lib/memeages-back-stack';

const app = new cdk.App();
new MemeagesBackStack(app, 'MemeagesBackStack');
