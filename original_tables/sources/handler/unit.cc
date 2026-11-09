#include "aodv-routing-protocol.h"
#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/wifi-module.h"
#include "ns3/mobility-module.h"
#include "ns3/aodv-helper.h"
#include <fstream>
#include <iostream>
using namespace ns3;
namespace ns3::aodv {
class DiagnosticAccess {
public:
 static void Insert(Ptr<RoutingProtocol>r, const RoutingTableEntry&e){r->m_routingTable.m_ipv4AddressEntry[e.GetDestination()]=e;}
 static RoutingTableEntry Snapshot(Ptr<RoutingProtocol>r,Ipv4Address dst){return r->m_routingTable.m_ipv4AddressEntry.at(dst);}
 static void Call(Ptr<RoutingProtocol>r,Ptr<Packet>p,Ipv4Address receiver,Ipv4Address sender){r->RecvRequest(p,receiver,sender);}
};}
int main(int argc,char**argv){std::string out="unit.csv";CommandLine cmd;cmd.AddValue("out","output CSV",out);cmd.Parse(argc,argv);std::ofstream f(out);NS_ABORT_MSG_IF(!f.good(),"output open failed");f<<"request_id,flag,next_same,seq_case,cache_valid,request_seq,D,TTL,post_flag,post_seq,post_valid,post_next,post_lifetime,simulation_time_ns\n";uint32_t id=0;
for(int flag=0;flag<3;flag++)for(int same=0;same<2;same++)for(int sc=0;sc<4;sc++)for(int D=0;D<2;D++)for(int ttl=1;ttl<=2;ttl++)for(int cacheValid=1;cacheValid>=0;cacheValid--){
 if(!cacheValid && !(same==1 && sc==1 && D==0 && ttl==2))continue;
 ++id;RngSeedManager::SetSeed(20261030);RngSeedManager::SetRun(1);NodeContainer nodes;nodes.Create(1);WifiHelper wifi;wifi.SetStandard(WIFI_STANDARD_80211g);YansWifiChannelHelper channel=YansWifiChannelHelper::Default();YansWifiPhyHelper phy;phy.SetChannel(channel.Create());WifiMacHelper mac;mac.SetType("ns3::AdhocWifiMac");auto devices=wifi.Install(phy,mac,nodes);MobilityHelper mob;mob.SetMobilityModel("ns3::ConstantPositionMobilityModel");mob.Install(nodes);AodvHelper aodv;InternetStackHelper internet;internet.SetRoutingHelper(aodv);internet.Install(nodes);Ipv4AddressHelper ips;ips.SetBase("10.1.1.0","255.255.255.0","0.0.0.2");auto addresses=ips.Assign(devices);auto ipv4=nodes.Get(0)->GetObject<Ipv4>();auto routing=DynamicCast<aodv::RoutingProtocol>(ipv4->GetRoutingProtocol());NS_ABORT_MSG_IF(!routing,"real AODV absent");aodv.AssignStreams(nodes,2000);Simulator::Stop(NanoSeconds(1));Simulator::Run();
 Ipv4Address receiver("10.1.1.2"),sender("10.1.1.1"),dst("10.1.1.4"),next(same?"10.1.1.1":"10.1.1.3");aodv::RoutingTableEntry entry(devices.Get(0),dst,cacheValid,10,ipv4->GetAddress(1,0),2,next,Seconds(100));entry.SetFlag(static_cast<aodv::RouteFlags>(flag));aodv::DiagnosticAccess::Insert(routing,entry);
 aodv::RreqHeader req;req.SetId(id);req.SetOrigin(Ipv4Address("10.1.1.9"));req.SetOriginSeqno(20);req.SetDst(dst);req.SetDstSeqno(sc==0?0:sc==1?9:sc==2?10:11);req.SetUnknownSeqno(sc==0);req.SetDestinationOnly(D);req.SetGratuitousRrep(false);req.SetHopCount(0);auto p=Create<Packet>();p->AddHeader(req);SocketIpTtlTag tag;tag.SetTtl(ttl);p->AddPacketTag(tag);aodv::DiagnosticAccess::Call(routing,p,receiver,sender);auto after=aodv::DiagnosticAccess::Snapshot(routing,dst);
 f<<id<<","<<flag<<","<<same<<","<<sc<<","<<cacheValid<<","<<req.GetDstSeqno()<<","<<D<<","<<ttl<<","<<int(after.GetFlag())<<","<<after.GetSeqNo()<<","<<after.GetValidSeqNo()<<","<<after.GetNextHop()<<","<<after.GetLifeTime().GetSeconds()<<","<<Simulator::Now().GetNanoSeconds()<<"\n";
 Simulator::Destroy();
}
f.close();std::cout<<"cases="<<id<<"\n";return 0;}
