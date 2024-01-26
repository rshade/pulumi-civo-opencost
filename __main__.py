import pulumi
import pulumi_kubernetes as kubernetes
import pulumi_civo as civo
from typing import Dict, Any

# Create a Civo Kubernetes cluster
class CivoKubernetesCluster(pulumi.ComponentResource):
    def __init__(self, name: str, args: civo.KubernetesClusterArgs, opts=None):
        super().__init__('civo:kubernetes:Cluster', name, {}, opts)

        # Use the Civo provider plugin to create a Kubernetes cluster
        # Note: This resource definition assumes the Civo Pulumi provider plugin exists.
        # You must configure the Civo provider with the required credentials.
        self.cluster = civo.KubernetesCluster(name, args)

        # Get the cluster kubeconfig
        self.kubeconfig = self.cluster.kubeconfig

        # Create a Kubernetes provider instance using the kubeconfig from the created Civo cluster
        k8s_provider = kubernetes.Provider("k8s-provider", kubeconfig=self.cluster.kubeconfig)

        # Install OpenCost using Helm on the newly created Civo Kubernetes cluster
        self.open_cost_chart = kubernetes.helm.v3.Chart("opencost",
            kubernetes.helm.v3.ChartOpts(
                chart="cost-analyzer",
                version="1.82.0",  # Use the appropriate version of OpenCost
                fetch_opts=kubernetes.helm.v3.FetchOpts(
                    repo="https://helm.opencost.io",
                ),
                values={
                    "global": {
                        "clusterName": self.cluster.name,
                    },
                },
            ),
            opts=pulumi.ResourceOptions(provider=k8s_provider),
)
        # Register the kubeconfig as an output of this component
        self.register_outputs({"kubeconfig": self.kubeconfig})


# Create a network
custom_net = civo.Network("customNet", label="my-custom-network")
# Create a firewall

fw = civo.Firewall("wwwIndex/firewallFirewall",
    network_id=custom_net.id,
    create_default_rules=True)

# Define the arguments for creating the cluster
cluster_args = civo.KubernetesClusterArgs(
    # Specify the required arguments for the cluster
    region="LON1",
    firewall_id=fw.id,
    kubernetes_version="1.21.0-k3s1",
    pools=civo.KubernetesClusterPoolsArgs(
        node_count=3,
        size="g3.k3s.medium",
    ),
    applications="Traefik, Helm",  # Make sure Helm is installed on the cluster
)

# Create a Civo Kubernetes cluster instance
civo_cluster = CivoKubernetesCluster("my-civo-cluster", cluster_args)

# Export the Civo cluster's kubeconfig
pulumi.export("kubeconfig", civo_cluster.kubeconfig)