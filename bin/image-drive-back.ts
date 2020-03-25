#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from '@aws-cdk/core';
import { ImageDriveBackStack } from '../lib/image-drive-back-stack';

const app = new cdk.App();
new ImageDriveBackStack(app, 'ImageDriveBackStack');
