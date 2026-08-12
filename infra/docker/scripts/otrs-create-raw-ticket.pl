#!/usr/bin/env perl
use strict;
use warnings;

use lib '/opt/otrs';
use lib '/opt/otrs/Kernel/cpan-lib';
use lib '/opt/otrs/Custom';

use Kernel::Config;
use Kernel::System::Encode;
use Kernel::System::Log;
use Kernel::System::Main;
use Kernel::System::Time;
use Kernel::System::DB;
use Kernel::System::Ticket;

my $Title = $ARGV[0];
if ( !defined $Title || $Title eq '' ) {
    print STDERR "Usage: otrs-create-raw-ticket.pl <title>\n";
    exit 2;
}

my %CommonObject;
$CommonObject{ConfigObject} = Kernel::Config->new();
$CommonObject{ConfigObject}->Set(
    Key   => 'SendmailModule',
    Value => 'Kernel::System::Email::DoNotSendEmail',
);
$CommonObject{EncodeObject} = Kernel::System::Encode->new(%CommonObject);
$CommonObject{LogObject}    = Kernel::System::Log->new(
    LogPrefix => 'OTRS-CreateRawTicket',
    %CommonObject,
);
$CommonObject{MainObject}   = Kernel::System::Main->new(%CommonObject);
$CommonObject{TimeObject}   = Kernel::System::Time->new(%CommonObject);
$CommonObject{DBObject}     = Kernel::System::DB->new(%CommonObject);
$CommonObject{TicketObject} = Kernel::System::Ticket->new(%CommonObject);

my $TicketID = $CommonObject{TicketObject}->TicketCreate(
    Title        => $Title,
    Queue        => 'Raw',
    Lock         => 'unlock',
    Priority     => '3 normal',
    State        => 'new',
    CustomerID   => 'ilegra-poc',
    CustomerUser => 'poc@example.com',
    OwnerID      => 1,
    UserID       => 1,
);
if ( !$TicketID ) {
    print STDERR "TicketCreate failed for title=$Title\n";
    exit 1;
}

my $ArticleID = $CommonObject{TicketObject}->ArticleCreate(
    TicketID       => $TicketID,
    ArticleType    => 'note-external',
    SenderType     => 'customer',
    From           => 'poc@example.com',
    To             => 'raw@localhost',
    Subject        => $Title,
    Body           => "Ticket smoke PoC Google Chat.\nTitle: $Title\n",
    ContentType    => 'text/plain; charset=utf-8',
    HistoryType    => 'NewTicket',
    HistoryComment => 'Created by docker-smoke',
    UserID         => 1,
    NoAgentNotify  => 1,
);
if ( !$ArticleID ) {
    print STDERR "ArticleCreate failed for TicketID=$TicketID\n";
    exit 1;
}

my %Ticket = $CommonObject{TicketObject}->TicketGet(
    TicketID => $TicketID,
    UserID   => 1,
);

print "$TicketID\t$Ticket{TicketNumber}\t$Ticket{Queue}\n";
exit 0;
