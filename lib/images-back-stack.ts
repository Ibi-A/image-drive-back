import * as cdk from "@aws-cdk/core";
import { LambdaRestApi } from "@aws-cdk/aws-apigateway";
import { Table, AttributeType } from "@aws-cdk/aws-dynamodb";
import {
  Function as LambdaFunction,
  Runtime as LambdaRuntime,
  Code as LambdaSourceCode,
  LayerVersion
} from "@aws-cdk/aws-lambda";
import { Bucket } from "@aws-cdk/aws-s3";


enum ResourceType {
  S3_BUCKET,
  LAMBDA,
  LAYER,
  DYNAMODB_TABLE,
  API
}

class Utilities {
  /** JSON containing the name of every resources in the project */
  public static RESOURCE_NAMES = require("../conf/resource-names.json");
  /** Path of the folder containing the Lambdas source code files */
  public static LAMBDA_SOURCE_CODE_FOLDER = __dirname + "/lambdas";
  /** Default Lambda handler function name for every Lambda functions */
  public static LAMBDA_HANDLER_NAME = "lambda_handler";
  /** Path of the folder containing the Lambdas layers */
  public static LAMBDA_LAYERS_FOLDER = Utilities.LAMBDA_SOURCE_CODE_FOLDER + "/layers";
  /** Path of the configuration layer folder */
  public static CONFIGURATION_LAYER_FOLDER = Utilities.LAMBDA_LAYERS_FOLDER + "/configuration-layer";

  /** JSON containing the name of every AWS resources in the project */
  public static IMAGES_CRUD_LAMBDA_ENV_VAR_NAMES = require(Utilities.CONFIGURATION_LAYER_FOLDER +
    "/lambda-environment-variable-names/images-crud-lambda.json");
  /** Resource identifier of the images CRUD Lambda handler */
  public static IMAGES_CRUD_LAMBDA_HANDLER = "images_crud_lambda" + "." + Utilities.LAMBDA_HANDLER_NAME; 

  public static getResourceNameById(resourceType: ResourceType, resourceId: string) {

    let resourceName = ""

    switch (+resourceType) {
      case ResourceType.S3_BUCKET:
        resourceName = Utilities.RESOURCE_NAMES.s3.find((bucket: any) => bucket.bucketId === resourceId)["bucketName"]
        break

      case ResourceType.LAMBDA:
        resourceName = Utilities.RESOURCE_NAMES.lambda.find((lambda: any) => lambda.lambdaId === resourceId)["lambdaName"]
        break

      case ResourceType.LAYER:
        resourceName = Utilities.RESOURCE_NAMES.layer.find((layer: any) => layer.layerId === resourceId)["layerName"]
        break

      case ResourceType.DYNAMODB_TABLE:
        resourceName = Utilities.RESOURCE_NAMES.dynamoDb.find((table: any) => table.tableId === resourceId)["tableName"]
        break

      case ResourceType.API:
        resourceName = Utilities.RESOURCE_NAMES.apiGw.find((api: any) => api.apiId === resourceId)["apiName"]
        break
    }

    return resourceName
  }

}

export class ImagesBackStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    console.log('[*] Constructing the main stack...')

    // create a S3 bucket containing all the images (image files)
    console.log('[*] Creating ' + 'imagesBucket' + '...')
    const bucket = new Bucket(this, Utilities.getResourceNameById(ResourceType.S3_BUCKET, 'imagesBucket'))
    
    // instanciate the configuration layer for the images CRUD Lambda function
    console.log('[*] Creating ' + 'imagesCrudLayer' + '...')
    const configLayer = new LayerVersion(
      this,
      Utilities.getResourceNameById(ResourceType.LAYER, "imagesCrudLayer"),
      {
        compatibleRuntimes: [LambdaRuntime.PYTHON_3_8],
        code: LambdaSourceCode.fromAsset(Utilities.CONFIGURATION_LAYER_FOLDER)
      }
    );

    // create a Lambda function handling basic CRUD operations on the images in the S3 folder
    console.log('[*] Creating ' + 'imagesCrudLambda' + '...')
    const crudLambda = new LambdaFunction(
      this,
      Utilities.getResourceNameById(ResourceType.LAMBDA, "imagesCrudLambda"),
      {
        runtime: LambdaRuntime.PYTHON_3_8,
        handler: Utilities.IMAGES_CRUD_LAMBDA_HANDLER,
        code: LambdaSourceCode.fromAsset(Utilities.LAMBDA_SOURCE_CODE_FOLDER),
        layers: [configLayer]
      }
    );

    // create a DynamoDB table storing information regarding the uploaded images in the S3 bucket
    console.log('[*] Creating ' + 'imagesInformationTable' + '...')
    const informationTable = new Table(
      this,
      Utilities.getResourceNameById(ResourceType.DYNAMODB_TABLE, "imagesInformationTable"),
      {
        partitionKey: {
          name: "name",
          type: AttributeType.STRING
        }
      }
    );

    // create a REST API backed by the previously created CRUD Lambda function
    console.log('[*] Creating ' + 'imagesApi' + '...')
    const api = this.initImagesApi(crudLambda);

    // add environment variables to access the S3 bucket and the DynamoDB table
    crudLambda.addEnvironment(
      Utilities.IMAGES_CRUD_LAMBDA_ENV_VAR_NAMES[0],
      bucket.bucketName
    );
    crudLambda.addEnvironment(
      Utilities.IMAGES_CRUD_LAMBDA_ENV_VAR_NAMES[1],
      informationTable.tableName
    );

    console.log('[*] Success!')
  }

  /** Returns a configured API with specific routes to access images */
  private initImagesApi(crudLambda: LambdaFunction) {
    let api = new LambdaRestApi(this, Utilities.getResourceNameById(ResourceType.API, "imagesApi"), {
      handler: crudLambda,
      proxy: false
    });

    const images = api.root.addResource("images");
    images.addMethod("GET");
    images.addMethod("POST");

    const image = images.addResource("{images-name}");
    image.addMethod("GET");
    image.addMethod("PUT");
    image.addMethod("PATCH");
    image.addMethod("DELETE");

    return api;
  }
}
