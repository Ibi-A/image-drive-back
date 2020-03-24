import * as cdk from '@aws-cdk/core';
import { LambdaRestApi } from '@aws-cdk/aws-apigateway';
import { Table, AttributeType } from '@aws-cdk/aws-dynamodb';
import { Function as LambdaFunction, Runtime as LambdaRuntime, Code as LambdaSourceCode, LayerVersion } from '@aws-cdk/aws-lambda';
import { Bucket } from '@aws-cdk/aws-s3';


class Utilities {

  /** JSON containing the name of every resources in the project */
  public static RESOURCE_NAMES = require("../conf/resource-names.json")
  /** Path of the folder containing the Lambdas source code files */
  public static LAMBDA_SOURCE_CODE_FOLDER = __dirname + "\\lambdas\\"
  /** Path of the folder containing the Lambdas layers files */
  public static LAMBDA_LAYERS_FOLDER = __dirname + "\\lambdas\\" + "\\layers\\"
  /** Default Lambda handler function name for every Lambda functions */
  public static LAMBDA_HANDLER_NAME = "lambda_handler"
  
  /** Returns the Lambda handler name (string) for a given Lambda source code filename WITHOUT FILE EXTENSION (string) */
  public static getLambdaHandlerByLambdaSourceCodeFilename(lambdaSourceCodeFilename: string) {
    return lambdaSourceCodeFilename + "." + Utilities.LAMBDA_HANDLER_NAME
  }
}


export class MemeagesBackStack extends cdk.Stack {

  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // create a S3 bucket containing all the memes (image files)
    const bucket = new Bucket(this, Utilities.RESOURCE_NAMES.s3.memesBucket)

    // create a Lambda layer containing boto3
    const crudLambdaLayer = new LayerVersion(this, Utilities.RESOURCE_NAMES.layer.memesCrudLambda, {
      code: LambdaSourceCode.fromAsset(Utilities.LAMBDA_LAYERS_FOLDER),
      compatibleRuntimes: [LambdaRuntime.PYTHON_3_8],
      description: 'Layer for CRUD memes Lambda containing boto3'
    })

    // create a Lambda function handling basic CRUD operations on the memes in the S3 folder
    const crudLambda = new LambdaFunction(this, Utilities.RESOURCE_NAMES.lambda.memesCrudLambda.lambdaName, {
      runtime: LambdaRuntime.PYTHON_3_8,
      handler: Utilities.getLambdaHandlerByLambdaSourceCodeFilename(Utilities.RESOURCE_NAMES.lambda.memesCrudLambda.lambdaSourceCode),
      code: LambdaSourceCode.fromAsset(Utilities.LAMBDA_SOURCE_CODE_FOLDER),
      layers: [crudLambdaLayer]
    })

    // create a DynamoDB table storing information regarding the uploaded memes in the S3 bucket
    const informationTable = new Table(this, Utilities.RESOURCE_NAMES.dynamoDb.memesInformationTable, {
      partitionKey: {
        name: 'name',
        type: AttributeType.STRING
      }
    })

    // create a REST API backed by the previously created CRUD Lambda function
    const api = this.initMemesApi(crudLambda)
  }


  /** Returns a configured API with specific routes to access memes */
  private initMemesApi(crudLambda: LambdaFunction) {
    let api = new LambdaRestApi(this, Utilities.RESOURCE_NAMES.apiGw.memesApi, {
      handler: crudLambda,
      proxy: false
    })
    
    const memes = api.root.addResource("memes")
    memes.addMethod("GET")
    memes.addMethod("POST")

    const meme = memes.addResource("{meme-name}")
    meme.addMethod("GET")
    meme.addMethod("PUT")
    meme.addMethod("DELETE")

    return api
  }
}
