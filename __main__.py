import pulumi
import pulumi_aws as aws
import os

instance_type = "t2.micro"
ami_id = "ami-01811d4912b4ccb26"
key_name = "ssh-key"

# Create a VPC
vpc = aws.ec2.Vpc(
    f"aws-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={"Name": f"aws-vpc"}
)

# Create an Internet Gateway
igw = aws.ec2.InternetGateway(
    f"aws-igw",
    vpc_id=vpc.id,
    tags={"Name": f"aws-igw"}
)

# Create a public subnet
subnet = aws.ec2.Subnet(
    f"aws-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    map_public_ip_on_launch=True,
    tags={"Name": f"aws-subnet"}
)

# Create a route table for public access
route_table = aws.ec2.RouteTable(
    f"aws-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        )
    ],
    tags={"Name": f"aws-rt"}
)

# Associate the route table with the subnet
route_table_assoc = aws.ec2.RouteTableAssociation(
    f"aws-rt-assoc",
    subnet_id=subnet.id,
    route_table_id=route_table.id
)

# Create a security group
security_group = aws.ec2.SecurityGroup(
    f"aws-sg",
    vpc_id=vpc.id,
    description="Security group for aws instances",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"]
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"]
        )
    ],
    tags={"Name": f"aws-sg"}
)

node_count = 1
instances = []
for i in range(node_count):
    instance = aws.ec2.Instance(
        f"instance-{i}",
        instance_type=instance_type,
        ami=ami_id,
        subnet_id=subnet.id,
        vpc_security_group_ids=[security_group.id],
        key_name=key_name,
        associate_public_ip_address=True,
        private_ip=f"10.0.1.2{i}",
        tags={"Name": f"instance-{i}"},
        opts=pulumi.ResourceOptions(
            depends_on=[
                route_table_assoc,
                subnet
            ]
        )
    )
    instances.append(instance)

# Export Public and Private IPs of Controller and Worker Instances
instance_public_ips = [instance.public_ip for instance in instances]
instance_private_ips = [instance.private_ip for instance in instances]

pulumi.export('instance_public_ips', instance_public_ips)
pulumi.export('instance_private_ips', instance_private_ips)

# Export the VPC ID and Subnet ID for reference
pulumi.export('vpc_id', vpc.id)
pulumi.export('subnet_id', subnet.id)
